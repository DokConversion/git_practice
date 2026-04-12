#!/usr/bin/env node

/**
 * CLI fuer den Video Analyzer.
 *
 * Nutzung:
 *   npx ts-node src/analyzer/cli.ts <video-datei>
 *   npm run analyze -- <video-datei>
 */

import { VideoAnalyzer } from "./video-analyzer";
import * as path from "path";

async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.log(`
╔══════════════════════���═══════════════════╗
║       🎬 Video Analyzer Agent           ║
║   Analyse von Referenzvideos fuer       ║
║   professionelle Remotion-Reproduktion  ║
╚══════════════════════════════════════════╝

Nutzung:
  npm run analyze <video-datei>

Beispiel:
  npm run analyze assets/videos/referenz.mp4

Analysiert:
  • Technische Metadaten (Codec, FPS, Resolution)
  • Szenenwechsel & Schnitte
  • B-Roll vs. Talking-Head Segmente
  • Pacing & Schnittrhythmus
  • Empfehlungen fuer Remotion-Reproduktion
`);
    process.exit(0);
  }

  const videoPath = path.resolve(args[0]);
  console.log(`Video-Analyzer startet...`);

  try {
    const analyzer = new VideoAnalyzer(videoPath);
    const report = await analyzer.analyze();

    // Zusammenfassung ausgeben
    console.log("\n" + report.summary);

    // Empfehlungen
    console.log("\n--- Remotion-Empfehlungen ---");
    report.recommendations.forEach((rec, i) => {
      console.log(`  ${i + 1}. ${rec}`);
    });

    // Scene Changes Details
    if (report.sceneChanges.length > 0) {
      console.log(`\n--- Szenenwechsel (${report.sceneChanges.length} erkannt) ---`);
      report.sceneChanges.slice(0, 20).forEach((sc, i) => {
        const mins = Math.floor(sc.timestamp / 60);
        const secs = (sc.timestamp % 60).toFixed(2);
        console.log(
          `  ${String(i + 1).padStart(3)}. ${String(mins).padStart(2, "0")}:${secs.padStart(5, "0")} (Frame ${sc.frame})`
        );
      });
      if (report.sceneChanges.length > 20) {
        console.log(
          `  ... und ${report.sceneChanges.length - 20} weitere Szenenwechsel`
        );
      }
    }

    // Segment-Details
    console.log(`\n--- Segmente (${report.segments.length}) ---`);
    report.segments.slice(0, 15).forEach((seg, i) => {
      const typeLabel =
        seg.type === "b-roll-candidate"
          ? "B-Roll"
          : seg.type === "talking-head-candidate"
            ? "Talking"
            : "Szene";
      console.log(
        `  ${String(i + 1).padStart(3)}. [${typeLabel.padEnd(7)}] ${seg.start.toFixed(1)}s - ${seg.end.toFixed(1)}s (${seg.duration.toFixed(1)}s)`
      );
    });
    if (report.segments.length > 15) {
      console.log(`  ... und ${report.segments.length - 15} weitere Segmente`);
    }

    // JSON-Report speichern
    const reportPath = path.join(
      path.dirname(videoPath),
      `${path.basename(videoPath, path.extname(videoPath))}_analysis.json`
    );
    const { writeFileSync } = await import("fs");
    writeFileSync(reportPath, JSON.stringify(report, null, 2));
    console.log(`\n✅ Vollstaendiger Report gespeichert: ${reportPath}`);
  } catch (error: any) {
    console.error(`\n❌ Fehler: ${error.message}`);
    process.exit(1);
  }
}

main();
