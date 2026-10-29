import Foundation
import CoreGraphics
import AppKit

guard CommandLine.arguments.count == 2, let pid = Int32(CommandLine.arguments[1]) else {
    fatalError("Expected the owned capture process PID")
}
guard CGPreflightScreenCaptureAccess() else {
    fatalError("Screen recording permission is not granted")
}
guard let application = NSRunningApplication(processIdentifier: pid),
      application.activate(options: [.activateAllWindows, .activateIgnoringOtherApps]) else {
    fatalError("Could not activate the owned capture application")
}
Thread.sleep(forTimeInterval: 0.8)
let windows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
let owned = windows.filter {
    ($0[kCGWindowOwnerPID as String] as? Int32) == pid &&
    ($0[kCGWindowLayer as String] as? Int) == 0
}
let data = try JSONSerialization.data(withJSONObject: owned, options: [.prettyPrinted, .sortedKeys])
FileHandle.standardOutput.write(data)
