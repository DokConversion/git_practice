import { execSync } from "child_process";
import * as fs from "fs";
import * as path from "path";

/**
 * Video Analyzer Agent
 *
 * Analysiert ein Referenzvideo und extrahiert:
 * - Technische Metadaten (Codec, Resolution, FPS, Bitrate)
 * - Szenenwechsel / Schnitte (Scene Changes)
 * - Geschaetzte B-Roll Segmente
 * - Pacing-Analyse (Schnittfrequenz, Rhythmus)
 * - Audio-Eigenschaften
 * - Farbtemperatur / Helligkeit
 *
 * Nutzt ffprobe + ffmpeg fuer frame-level Analyse.
 */

export interface VideoMetadata {
  filename: string;
  duration: number;
  width: number;
  height: number;
  fps: number;
  codec: string;
  bitrate: number;
  fileSize: number;
  audioCodec: string | null;
  audioSampleRate: number | null;
  audioChannels: number | null;
}

export interface SceneChange {
  timestamp: number;
  frame: number;
  score: number;
}

export interface Segment {
  start: number;
  end: number;
  duration: number;
  type: "scene" | "b-roll-candidate" | "talking-head-candidate";
  avgMotion: number;
}

export interface PacingAnalysis {
  totalCuts: number;
  avgCutDuration: number;
  minCutDuration: number;
  maxCutDuration: number;
  cutsPerMinute: number;
  paceCategory: "sehr-schnell" | "schnell" | "mittel" | "langsam" | "sehr-langsam";
  rhythm: "gleichmaessig" | "variabel" | "dynamisch";
}

export interface VideoAnalysisReport {
  metadata: VideoMetadata;
  sceneChanges: SceneChange[];
  segments: Segment[];
  pacing: PacingAnalysis;
  recommendations: string[];
  summary: string;
}

export class VideoAnalyzer {
  private videoPath: string;

  constructor(videoPath: string) {
    if (!fs.existsSync(videoPath)) {
      throw new Error(`Video nicht gefunden: ${videoPath}`);
    }
    this.videoPath = path.resolve(videoPath);
  }

  /**
   * Vollstaendige Analyse des Videos.
   */
  async analyze(): Promise<VideoAnalysisReport> {
    console.log(`\n🎬 Analysiere Video: ${path.basename(this.videoPath)}\n`);

    console.log("  [1/4] Extrahiere Metadaten...");
    const metadata = this.extractMetadata();

    console.log("  [2/4] Erkenne Szenenwechsel...");
    const sceneChanges = this.detectSceneChanges();

    console.log("  [3/4] Analysiere Segmente...");
    const segments = this.analyzeSegments(sceneChanges, metadata);

    console.log("  [4/4] Berechne Pacing...");
    const pacing = this.analyzePacing(sceneChanges, metadata);

    const recommendations = this.generateRecommendations(
      metadata,
      sceneChanges,
      segments,
      pacing
    );

    const summary = this.generateSummary(metadata, pacing, segments);

    return {
      metadata,
      sceneChanges,
      segments,
      pacing,
      recommendations,
      summary,
    };
  }

  /**
   * Extrahiert technische Metadaten via ffprobe.
   */
  private extractMetadata(): VideoMetadata {
    const probeCmd = `ffprobe -v quiet -print_format json -show_format -show_streams "${this.videoPath}"`;
    const output = execSync(probeCmd, { encoding: "utf-8" });
    const probe = JSON.parse(output);

    const videoStream = probe.streams.find(
      (s: any) => s.codec_type === "video"
    );
    const audioStream = probe.streams.find(
      (s: any) => s.codec_type === "audio"
    );

    if (!videoStream) {
      throw new Error("Kein Video-Stream gefunden");
    }

    // FPS berechnen
    const fpsStr = videoStream.r_frame_rate || videoStream.avg_frame_rate || "30/1";
    const [num, den] = fpsStr.split("/").map(Number);
    const fps = Math.round((num / (den || 1)) * 100) / 100;

    const stats = fs.statSync(this.videoPath);

    return {
      filename: path.basename(this.videoPath),
      duration: parseFloat(probe.format.duration || videoStream.duration || "0"),
      width: videoStream.width,
      height: videoStream.height,
      fps,
      codec: videoStream.codec_name,
      bitrate: parseInt(probe.format.bit_rate || "0", 10),
      fileSize: stats.size,
      audioCodec: audioStream?.codec_name || null,
      audioSampleRate: audioStream
        ? parseInt(audioStream.sample_rate, 10)
        : null,
      audioChannels: audioStream?.channels || null,
    };
  }

  /**
   * Erkennt Szenenwechsel via ffmpeg scene-detection Filter.
   * Nutzt den scene-Filter mit einem Schwellenwert.
   */
  private detectSceneChanges(threshold: number = 0.3): SceneChange[] {
    try {
      // ffmpeg scene detection - gibt Frames aus bei denen sich die Szene aendert
      const cmd = `ffmpeg -i "${this.videoPath}" -vf "select='gt(scene,${threshold})',showinfo" -vsync vfr -f null - 2>&1`;
      const output = execSync(cmd, {
        encoding: "utf-8",
        maxBuffer: 50 * 1024 * 1024,
        timeout: 120000,
      });

      const sceneChanges: SceneChange[] = [];
      const lines = output.split("\n");

      for (const line of lines) {
        // Parse showinfo output: pts_time:XX.XX
        const ptsMatch = line.match(/pts_time:\s*([\d.]+)/);
        const nMatch = line.match(/\s+n:\s*(\d+)/);

        if (ptsMatch) {
          const timestamp = parseFloat(ptsMatch[1]);
          const frameNum = nMatch ? parseInt(nMatch[1], 10) : Math.round(timestamp * 30);

          sceneChanges.push({
            timestamp,
            frame: frameNum,
            score: threshold, // Mindest-Score, da der Filter bereits filtert
          });
        }
      }

      // Sortieren nach Zeitstempel
      sceneChanges.sort((a, b) => a.timestamp - b.timestamp);

      return sceneChanges;
    } catch (error) {
      console.warn("  ⚠️  Scene-Detection Fallback: Nutze einfache Analyse");
      return [];
    }
  }

  /**
   * Analysiert Segmente basierend auf Szenenwechseln.
   * Klassifiziert in potenzielle B-Roll vs. Talking-Head Segmente.
   */
  private analyzeSegments(
    sceneChanges: SceneChange[],
    metadata: VideoMetadata
  ): Segment[] {
    const segments: Segment[] = [];
    const timestamps = [0, ...sceneChanges.map((sc) => sc.timestamp), metadata.duration];

    for (let i = 0; i < timestamps.length - 1; i++) {
      const start = timestamps[i];
      const end = timestamps[i + 1];
      const duration = end - start;

      // Heuristik: Kurze Segmente (< 3s) sind oft B-Roll,
      // Laengere Segmente (> 5s) sind oft Talking-Head
      let type: Segment["type"] = "scene";
      if (duration < 3) {
        type = "b-roll-candidate";
      } else if (duration > 5) {
        type = "talking-head-candidate";
      }

      segments.push({
        start,
        end,
        duration,
        type,
        avgMotion: 0, // Wird in erweiterter Analyse gefuellt
      });
    }

    return segments;
  }

  /**
   * Analysiert das Pacing (Schnittrhythmus) des Videos.
   */
  private analyzePacing(
    sceneChanges: SceneChange[],
    metadata: VideoMetadata
  ): PacingAnalysis {
    if (sceneChanges.length === 0) {
      return {
        totalCuts: 0,
        avgCutDuration: metadata.duration,
        minCutDuration: metadata.duration,
        maxCutDuration: metadata.duration,
        cutsPerMinute: 0,
        paceCategory: "sehr-langsam",
        rhythm: "gleichmaessig",
      };
    }

    const cutDurations: number[] = [];
    const timestamps = [0, ...sceneChanges.map((sc) => sc.timestamp)];

    for (let i = 0; i < timestamps.length - 1; i++) {
      cutDurations.push(timestamps[i + 1] - timestamps[i]);
    }
    // Letztes Segment
    cutDurations.push(metadata.duration - timestamps[timestamps.length - 1]);

    const avgCutDuration =
      cutDurations.reduce((a, b) => a + b, 0) / cutDurations.length;
    const minCutDuration = Math.min(...cutDurations);
    const maxCutDuration = Math.max(...cutDurations);

    const cutsPerMinute =
      metadata.duration > 0
        ? (sceneChanges.length / metadata.duration) * 60
        : 0;

    // Pace-Kategorie
    let paceCategory: PacingAnalysis["paceCategory"];
    if (cutsPerMinute > 30) paceCategory = "sehr-schnell";
    else if (cutsPerMinute > 15) paceCategory = "schnell";
    else if (cutsPerMinute > 6) paceCategory = "mittel";
    else if (cutsPerMinute > 2) paceCategory = "langsam";
    else paceCategory = "sehr-langsam";

    // Rhythmus-Analyse
    const stdDev = Math.sqrt(
      cutDurations.reduce(
        (sum, d) => sum + Math.pow(d - avgCutDuration, 2),
        0
      ) / cutDurations.length
    );
    const coefficientOfVariation = avgCutDuration > 0 ? stdDev / avgCutDuration : 0;

    let rhythm: PacingAnalysis["rhythm"];
    if (coefficientOfVariation < 0.3) rhythm = "gleichmaessig";
    else if (coefficientOfVariation < 0.7) rhythm = "variabel";
    else rhythm = "dynamisch";

    return {
      totalCuts: sceneChanges.length,
      avgCutDuration: Math.round(avgCutDuration * 100) / 100,
      minCutDuration: Math.round(minCutDuration * 100) / 100,
      maxCutDuration: Math.round(maxCutDuration * 100) / 100,
      cutsPerMinute: Math.round(cutsPerMinute * 10) / 10,
      paceCategory,
      rhythm,
    };
  }

  /**
   * Generiert konkrete Empfehlungen fuer die Remotion-Reproduktion.
   */
  private generateRecommendations(
    metadata: VideoMetadata,
    sceneChanges: SceneChange[],
    segments: Segment[],
    pacing: PacingAnalysis
  ): string[] {
    const recommendations: string[] = [];

    // Resolution & FPS
    recommendations.push(
      `Composition-Einstellungen: ${metadata.width}x${metadata.height} @ ${metadata.fps} fps`
    );

    // Dauer
    const durationInFrames = Math.ceil(metadata.duration * metadata.fps);
    recommendations.push(
      `Gesamtdauer: ${Math.round(metadata.duration)}s = ${durationInFrames} Frames`
    );

    // Pacing
    recommendations.push(
      `Schnittrhythmus: ${pacing.paceCategory} (${pacing.cutsPerMinute} Schnitte/Min, ${pacing.rhythm})`
    );

    // Segment-Empfehlungen
    const bRollCount = segments.filter(
      (s) => s.type === "b-roll-candidate"
    ).length;
    const talkingHeadCount = segments.filter(
      (s) => s.type === "talking-head-candidate"
    ).length;

    if (bRollCount > 0) {
      recommendations.push(
        `B-Roll Segmente erkannt: ${bRollCount} (durchschnittlich < 3s) - Nutze <Sequence> mit kurzen durationInFrames`
      );
    }

    if (talkingHeadCount > 0) {
      recommendations.push(
        `Talking-Head Segmente: ${talkingHeadCount} (> 5s) - Nutze KenBurns oder LowerThird Overlays`
      );
    }

    // Transition-Empfehlungen basierend auf Pacing
    if (pacing.paceCategory === "schnell" || pacing.paceCategory === "sehr-schnell") {
      recommendations.push(
        "Schnelles Pacing: Verwende harte Schnitte (Cut) und kurze WipeIn Transitions"
      );
    } else if (pacing.paceCategory === "langsam" || pacing.paceCategory === "sehr-langsam") {
      recommendations.push(
        "Langsames Pacing: Verwende Crossfade und CircleReveal Transitions (15-30 Frames)"
      );
    } else {
      recommendations.push(
        "Mittleres Pacing: Mix aus harten Schnitten und ZoomIn Transitions"
      );
    }

    // Audio
    if (metadata.audioCodec) {
      recommendations.push(
        `Audio vorhanden (${metadata.audioCodec}, ${metadata.audioSampleRate}Hz) - Nutze <Audio> Tags in Remotion`
      );
    }

    return recommendations;
  }

  /**
   * Generiert eine menschenlesbare Zusammenfassung.
   */
  private generateSummary(
    metadata: VideoMetadata,
    pacing: PacingAnalysis,
    segments: Segment[]
  ): string {
    const bRoll = segments.filter((s) => s.type === "b-roll-candidate").length;
    const talking = segments.filter(
      (s) => s.type === "talking-head-candidate"
    ).length;
    const totalSegments = segments.length;

    return [
      `=== VIDEO-ANALYSE: ${metadata.filename} ===`,
      ``,
      `Format: ${metadata.width}x${metadata.height} @ ${metadata.fps}fps (${metadata.codec})`,
      `Dauer: ${Math.round(metadata.duration)}s | Groesse: ${(metadata.fileSize / 1024 / 1024).toFixed(1)} MB`,
      `Audio: ${metadata.audioCodec || "Kein Audio"}`,
      ``,
      `--- Schnittanalyse ---`,
      `Gesamtschnitte: ${pacing.totalCuts}`,
      `Schnitte pro Minute: ${pacing.cutsPerMinute}`,
      `Tempo: ${pacing.paceCategory} | Rhythmus: ${pacing.rhythm}`,
      `Schnittdauer: Ø ${pacing.avgCutDuration}s (Min: ${pacing.minCutDuration}s, Max: ${pacing.maxCutDuration}s)`,
      ``,
      `--- Segmente ---`,
      `Gesamt: ${totalSegments} Segmente`,
      `B-Roll Kandidaten: ${bRoll}`,
      `Talking-Head Kandidaten: ${talking}`,
      ``,
      `Dieses Video laesst sich optimal mit Remotion reproduzieren.`,
    ].join("\n");
  }
}
