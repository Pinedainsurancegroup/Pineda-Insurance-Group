import Foundation
import CryptoKit

public enum CatalogParser {
    static func string(_ value: Any?) -> String {
        if let s = value as? String { return s }; if let n = value as? NSNumber { return n.stringValue }; return ""
    }
    static func trimmed(_ value: Any?) -> String { string(value).trimmingCharacters(in: .whitespacesAndNewlines) }
    static func imageURL(_ value: Any?, allowingInsecureHTTP: Bool = false) -> URL? {
        try? Endpoint.server(trimmed(value), playlist: true, allowingInsecureHTTP: allowingInsecureHTTP)
    }
    // PHP encodes an empty associative collection as {} and sometimes retains
    // numeric keys. Ignore malformed rows without discarding an otherwise valid catalog.
    static func rows(_ value: Any) throws -> [[String: Any]] {
        let values: [Any]
        if let array = value as? [Any] { values = array }
        else if let indexed = value as? [String: Any], indexed.keys.allSatisfy({ UInt64($0) != nil }) {
            values = indexed.keys.sorted(by: numericOrder).compactMap { indexed[$0] }
        } else { throw PimflexError.invalidResponse }
        let result = values.compactMap { $0 as? [String: Any] }
        guard values.isEmpty || !result.isEmpty else { throw PimflexError.invalidResponse }
        return result
    }
    static func numericOrder(_ lhs: String, _ rhs: String) -> Bool {
        let left = UInt64(lhs), right = UInt64(rhs)
        if let left, let right, left != right { return left < right }
        return lhs < rhs
    }
    static func mediaExtension(_ value: Any?) -> String {
        let ext = trimmed(value).lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "."))
        return ext.isEmpty ? "mp4" : ext
    }
    public static func authenticate(_ data: Data) throws -> String {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let user = root["user_info"] as? [String: Any] else { throw PimflexError.invalidResponse }
        guard ["1", "true"].contains(trimmed(user["auth"]).lowercased()) else { throw PimflexError.invalidCredentials }
        guard trimmed(user["status"]).lowercased() == "active" else { throw PimflexError.inactiveAccount }
        return trimmed(user["exp_date"])
    }
    public static func categories(_ data: Data) throws -> [Category] {
        let rows = try Self.rows(JSONSerialization.jsonObject(with: data))
        var seen = Set<String>()
        return rows.compactMap { row in
            let id = trimmed(row["category_id"])
            guard !id.isEmpty, seen.insert(id).inserted else { return nil }
            return Category(id: id, name: trimmed(row["category_name"]))
        }
    }
    public static func items(_ data: Data, kind: MediaKind, allowingInsecureHTTP: Bool = false) throws -> [MediaItem] {
        let rows = try Self.rows(JSONSerialization.jsonObject(with: data))
        var seen = Set<String>()
        return rows.compactMap { row in
            let id = trimmed(row[kind == .series ? "series_id" : "stream_id"])
            guard !id.isEmpty, seen.insert(id).inserted else { return nil }
            return MediaItem(providerID: id, name: trimmed(row["name"]), kind: kind,
                             categoryID: trimmed(row["category_id"]), artwork: imageURL(row["stream_icon"], allowingInsecureHTTP: allowingInsecureHTTP) ?? imageURL(row["cover"], allowingInsecureHTTP: allowingInsecureHTTP),
                             fileExtension: mediaExtension(row["container_extension"]))
        }
    }
    public static func episodes(_ data: Data, allowingInsecureHTTP: Bool = false) throws -> [MediaItem] {
        guard let root = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              let payload = root["episodes"] else { throw PimflexError.invalidResponse }
        let groups: [(String?, [[String: Any]])]
        if let seasons = payload as? [String: Any] {
            groups = try seasons.keys.sorted(by: numericOrder).map { season in
                (season, try rows(seasons[season]!))
            }
        } else if let array = payload as? [Any] {
            // Sequential season keys may arrive as an array; a flat episode array
            // instead uses each episode's own season. Empty arrays are valid.
            let nonempty = array.filter { !($0 is NSNull) }
            if nonempty.allSatisfy({ $0 is [String: Any] }) { groups = [(nil, try rows(nonempty))] }
            else {
                groups = try array.enumerated().compactMap { index, value in
                    if value is NSNull { return nil }
                    return (String(index), try rows(value))
                }
            }
        } else { throw PimflexError.invalidResponse }
        var seen = Set<String>()
        let entries = groups.flatMap { season, rows in rows.compactMap { row -> MediaItem? in
            let id = trimmed(row["id"])
            guard !id.isEmpty else { return nil }
            let info = row["info"] as? [String: Any] ?? [:]
            return MediaItem(providerID: id, name: trimmed(row["title"]), kind: .series,
                             artwork: imageURL(info["movie_image"], allowingInsecureHTTP: allowingInsecureHTTP), fileExtension: mediaExtension(row["container_extension"]),
                             season: Int(trimmed(row["season"])) ?? season.flatMap(Int.init), episode: Int(trimmed(row["episode_num"])))
        }}.sorted {
            ($0.season ?? 0, $0.episode ?? 0, $0.name, $0.providerID) < ($1.season ?? 0, $1.episode ?? 0, $1.name, $1.providerID)
        }
        return entries.filter { seen.insert($0.id).inserted }
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
        func date(_ value: Any?) -> Date? {
            guard let seconds = Double(CatalogParser.trimmed(value)), seconds.isFinite else { return nil }
            return Date(timeIntervalSince1970: seconds)
        }
        return rows.enumerated().map { index, row in
            Programme(id: "\(CatalogParser.string(row["id"]))-\(index)", title: decode(row["title"]),
                      description: decode(row["description"]), start: date(row["start_timestamp"]),
                      end: date(row["stop_timestamp"] ?? row["end_timestamp"]))
        }
    }
}

public enum M3UParser {
    public static func parse(_ text: String, baseURL: URL, allowingInsecureHTTP: Bool = false) throws -> [MediaItem] {
        let text = text.replacingOccurrences(of: "\u{feff}", with: "")
        let lines = text.components(separatedBy: .newlines).map { $0.trimmingCharacters(in: .whitespacesAndNewlines) }
        guard let header = lines.first(where: { !$0.isEmpty }), header.split(whereSeparator: \.isWhitespace).first == "#EXTM3U" else { throw PimflexError.invalidResponse }
        // A media HLS manifest is not an IPTV catalog.
        if lines.contains(where: { $0.hasPrefix("#EXT-X-TARGETDURATION:") || $0.hasPrefix("#EXT-X-STREAM-INF:") || $0.hasPrefix("#EXT-X-I-FRAME-STREAM-INF:") }) {
            let stream = try Endpoint.server(baseURL.absoluteString, playlist: true, allowingInsecureHTTP: allowingInsecureHTTP)
            return [MediaItem(providerID: digest(stream.absoluteString), name: "Transmisión", kind: .live, directURL: stream)]
        }
        var result: [MediaItem] = [], seen = Set<String>()
        var title = "", group = "", logo: URL?
        let regex = try NSRegularExpression(pattern: #"([\w-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')"#)
        for line in lines {
            if line.hasPrefix("#EXTINF:") {
                var quote: Character?; var separator: String.Index?
                for i in line.indices {
                    let character = line[i]
                    if character == "\"" || character == "'" {
                        if quote == character { quote = nil } else if quote == nil { quote = character }
                    }
                    if character == "," && quote == nil { separator = i; break }
                }
                title = separator.map { String(line[line.index(after: $0)...]).trimmingCharacters(in: .whitespaces) } ?? ""
                group = ""; logo = nil
                var metadataName = ""
                let metadata = separator.map { String(line[..<$0]) } ?? line
                for match in regex.matches(in: metadata, range: NSRange(metadata.startIndex..., in: metadata)) {
                    let key = String(metadata[Range(match.range(at: 1), in: metadata)!]).lowercased()
                    let range = match.range(at: 2).location != NSNotFound ? match.range(at: 2) : match.range(at: 3)
                    guard let valueRange = Range(range, in: metadata) else { continue }
                    let value = String(metadata[valueRange])
                    if key == "group-title" { group = value }
                    if key == "tvg-logo" { logo = CatalogParser.imageURL(value, allowingInsecureHTTP: allowingInsecureHTTP) }
                    if key == "tvg-name" { metadataName = value }
                }
                if title.isEmpty { title = metadataName }
            } else if line.hasPrefix("#EXTGRP:") {
                group = String(line.dropFirst("#EXTGRP:".count)).trimmingCharacters(in: .whitespaces)
            } else if !line.isEmpty && !line.hasPrefix("#") {
                defer { title = ""; group = ""; logo = nil }
                guard let resolved = URL(string: line, relativeTo: baseURL)?.absoluteURL,
                      let url = try? Endpoint.server(resolved.absoluteString, playlist: true, allowingInsecureHTTP: allowingInsecureHTTP),
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
