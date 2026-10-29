import Foundation
import CryptoKit

public enum CatalogParser {
    static func string(_ value: Any?) -> String {
        if let s = value as? String { return s }; if let n = value as? NSNumber { return n.stringValue }; return ""
    }
    static func imageURL(_ value: Any?) -> URL? {
        guard let url = URL(string: string(value)), url.scheme == "https" else { return nil }; return url
    }
    public static func authenticate(_ data: Data) throws -> String {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let user = root["user_info"] as? [String: Any] else { throw PimflexError.invalidResponse }
        guard string(user["auth"]) == "1" else { throw PimflexError.invalidCredentials }
        guard string(user["status"]).lowercased() == "active" else { throw PimflexError.inactiveAccount }
        return string(user["exp_date"])
    }
    public static func categories(_ data: Data) throws -> [Category] {
        guard let rows = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else { throw PimflexError.invalidResponse }
        var seen = Set<String>()
        return rows.compactMap { row in
            let id = string(row["category_id"])
            guard !id.isEmpty, seen.insert(id).inserted else { return nil }
            return Category(id: id, name: string(row["category_name"]))
        }
    }
    public static func items(_ data: Data, kind: MediaKind) throws -> [MediaItem] {
        guard let rows = try JSONSerialization.jsonObject(with: data) as? [[String: Any]] else { throw PimflexError.invalidResponse }
        var seen = Set<String>()
        return rows.compactMap { row in
            let id = string(row[kind == .series ? "series_id" : "stream_id"])
            guard !id.isEmpty, seen.insert(id).inserted else { return nil }
            let ext = string(row["container_extension"])
            return MediaItem(providerID: id, name: string(row["name"]), kind: kind,
                             categoryID: string(row["category_id"]), artwork: imageURL(row["stream_icon"] ?? row["cover"]),
                             fileExtension: ext.isEmpty ? "mp4" : ext)
        }
    }
    public static func episodes(_ data: Data) throws -> [MediaItem] {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let seasons = root["episodes"] as? [String: [[String: Any]]] else { throw PimflexError.invalidResponse }
        var seen = Set<String>()
        return seasons.flatMap { season, rows in rows.compactMap { row -> MediaItem? in
            let id = string(row["id"])
            guard !id.isEmpty, seen.insert(id).inserted else { return nil }
            let info = row["info"] as? [String: Any] ?? [:]
            let ext = string(row["container_extension"])
            return MediaItem(providerID: id, name: string(row["title"]), kind: .series,
                             artwork: imageURL(info["movie_image"]), fileExtension: ext.isEmpty ? "mp4" : ext,
                             season: Int(string(row["season"])) ?? Int(season), episode: Int(string(row["episode_num"])))
        }}.sorted { ($0.season ?? 0, $0.episode ?? 0, $0.name) < ($1.season ?? 0, $1.episode ?? 0, $1.name) }
    }
}

public struct Programme: Identifiable, Sendable {
    public let id: String
    public let title: String
    public let description: String
    public let start: Date?
    public let end: Date?
}
public enum EPGParser {
    public static func parse(_ data: Data) throws -> [Programme] {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let rows = root["epg_listings"] as? [[String: Any]] else { throw PimflexError.invalidResponse }
        func decode(_ value: Any?) -> String {
            let text = CatalogParser.string(value)
            return Data(base64Encoded: text).flatMap { String(data: $0, encoding: .utf8) } ?? text
        }
        func date(_ value: Any?) -> Date? { Double(CatalogParser.string(value)).map(Date.init(timeIntervalSince1970:)) }
        return rows.enumerated().map { index, row in
            Programme(id: "\(CatalogParser.string(row["id"]))-\(index)", title: decode(row["title"]),
                      description: decode(row["description"]), start: date(row["start_timestamp"]),
                      end: date(row["stop_timestamp"] ?? row["end_timestamp"]))
        }
    }
}

public enum M3UParser {
    public static func parse(_ text: String, baseURL: URL) throws -> [MediaItem] {
        let text = text.replacingOccurrences(of: "\u{feff}", with: "")
        guard text.trimmingCharacters(in: .whitespacesAndNewlines).hasPrefix("#EXTM3U") else { throw PimflexError.invalidResponse }
        // A media HLS manifest is not an IPTV catalog.
        if text.contains("#EXT-X-TARGETDURATION") || text.contains("#EXT-X-STREAM-INF") {
            return [MediaItem(providerID: digest(baseURL.absoluteString), name: "Transmisión", kind: .live, directURL: baseURL)]
        }
        var result: [MediaItem] = [], seen = Set<String>()
        var title = "", group = "", logo: URL?
        let regex = try NSRegularExpression(pattern: #"([\w-]+)="([^"]*)""#)
        for raw in text.components(separatedBy: .newlines) {
            let line = raw.trimmingCharacters(in: .whitespacesAndNewlines)
            if line.hasPrefix("#EXTINF:") {
                var quoted = false; var separator: String.Index?
                for i in line.indices { if line[i] == "\"" { quoted.toggle() }; if line[i] == "," && !quoted { separator = i; break } }
                title = separator.map { String(line[line.index(after: $0)...]) } ?? ""
                group = ""; logo = nil
                for match in regex.matches(in: line, range: NSRange(line.startIndex..., in: line)) {
                    let key = String(line[Range(match.range(at: 1), in: line)!])
                    let value = String(line[Range(match.range(at: 2), in: line)!])
                    if key == "group-title" { group = value }; if key == "tvg-logo" { logo = CatalogParser.imageURL(value) }
                }
            } else if !line.isEmpty && !line.hasPrefix("#") {
                defer { title = ""; group = ""; logo = nil }
                guard let url = URL(string: line, relativeTo: baseURL)?.absoluteURL, url.scheme == "https",
                      seen.insert(url.absoluteString).inserted else { continue }
                let ext = url.pathExtension.lowercased()
                let kind: MediaKind = ["mp4", "m4v", "mov", "mkv", "avi"].contains(ext) ? .movie : .live
                result.append(MediaItem(providerID: digest(url.absoluteString), name: title.isEmpty ? "Canal \(result.count + 1)" : title,
                                        kind: kind, categoryID: group, artwork: logo, fileExtension: ext, directURL: url))
            }
        }
        guard !result.isEmpty else { throw PimflexError.emptyPlaylist }; return result
    }
    private static func digest(_ text: String) -> String { SHA256.hash(data: Data(text.utf8)).map { String(format: "%02x", $0) }.joined() }
}
