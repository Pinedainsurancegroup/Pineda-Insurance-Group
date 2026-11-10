import Foundation

public enum PlaybackEngine: Equatable, Sendable {
    case native, compatible

    public static let compatibleExtensions: Set<String> = ["mkv", "avi", "flv", "wmv", "webm", "ts", "m2ts", "mpeg", "mpg"]

    public static func forMediaURL(_ url: URL) -> PlaybackEngine {
        compatibleExtensions.contains(url.pathExtension.lowercased()) ? .compatible : .native
    }
}
