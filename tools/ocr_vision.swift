// Apple Vision OCR for figure text (macOS only). Usage: swift tools/ocr_vision.swift IMAGE
// Prints a JSON array of {text, conf, box: [x, y, w, h]} in image pixels (top-left origin).
import Foundation
import Vision
import AppKit

let path = CommandLine.arguments[1]
guard let img = NSImage(contentsOfFile: path),
      let cg = img.cgImage(forProposedRect: nil, context: nil, hints: nil) else { exit(1) }
let W = Double(cg.width), H = Double(cg.height)
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.usesLanguageCorrection = false
try VNImageRequestHandler(cgImage: cg).perform([req])
var out: [[String: Any]] = []
for o in req.results ?? [] {
    guard let c = o.topCandidates(1).first else { continue }
    let b = o.boundingBox
    out.append(["text": c.string, "conf": c.confidence,
                "box": [Int(b.minX * W), Int((1 - b.maxY) * H), Int(b.width * W), Int(b.height * H)]])
}
print(String(data: try JSONSerialization.data(withJSONObject: out), encoding: .utf8)!)
