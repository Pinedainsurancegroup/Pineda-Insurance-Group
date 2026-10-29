import Foundation
import CryptoKit

public enum MediaKind: String, Codable, CaseIterable, Identifiable, Sendable {
    case live, movie, series
    public var id: String { rawValue }
    public var title: String {
        switch self { case .live: return "TV en vivo"; case .movie: return "Películas"; case .series: return "Series" }
    }
    public var categoryAction: String {
        switch self { case .live: return "get_live_categories"; case .movie: return "get_vod_categories"; case .series: return "get_series_categories" }
    }
    public var catalogAction: String {
        switch self { case .live: return "get_live_streams"; case .movie: return "get_vod_streams"; case .series: return "get_series" }
    }
}

public struct Category: Identifiable, Hashable, Sendable {
    public let id: String
    public let name: String
    public init(id: String, name: String) { self.id = id; self.name = name }
}

public struct MediaItem: Identifiable, Hashable, Codable, Sendable {
    public let id: String
    public let providerID: String
    public let name: String
    public let kind: MediaKind
    public let categoryID: String
    public let artwork: URL?
    public let fileExtension: String
    public let directURL: URL?
    public let season: Int?
    public let episode: Int?
    public init(providerID: String, name: String, kind: MediaKind, categoryID: String = "", artwork: URL? = nil,
                fileExtension: String = "mp4", directURL: URL? = nil, season: Int? = nil, episode: Int? = nil) {
        self.id = "\(kind.rawValue):\(providerID)"
        self.providerID = providerID; self.name = name; self.kind = kind; self.categoryID = categoryID
        self.artwork = artwork; self.fileExtension = fileExtension; self.directURL = directURL
        self.season = season; self.episode = episode
    }
}

public enum SourceMode: String, Codable, Sendable { case xtream, m3u }
public struct Account: Codable, Equatable, Sendable {
    public let mode: SourceMode
    public let server: URL
    public let username: String
    public let password: String
    public init(mode: SourceMode, server: URL, username: String = "", password: String = "") {
        self.mode = mode; self.server = server; self.username = username; self.password = password
    }
    // Namespaces history/favorites without persisting credentials in preferences.
    public var storageID: String {
        SHA256.hash(data: Data("\(mode.rawValue)|\(server.absoluteString)|\(username)".utf8))
            .map { String(format: "%02x", $0) }.joined()
    }
}

public enum PimflexError: Error, LocalizedError, Equatable {
    case invalidServer, insecureURL, invalidCredentials, inactiveAccount, invalidResponse, emptyPlaylist, unsupportedFormat, network, storage
    public var errorDescription: String? {
        switch self {
        case .invalidServer: return "Revisa la dirección HTTPS de tu servidor."
        case .insecureURL: return "Esta versión requiere una conexión HTTPS. Solicita la dirección segura a tu proveedor."
        case .invalidCredentials: return "El servidor no aceptó el usuario o la contraseña."
        case .inactiveAccount: return "Tu cuenta no está activa. Contacta a tu proveedor."
        case .invalidResponse: return "El servidor devolvió una respuesta que no pudimos leer."
        case .emptyPlaylist: return "La lista no contiene transmisiones HTTPS compatibles."
        case .unsupportedFormat: return "Este formato requiere otro motor de video. Pide a tu proveedor una versión HLS o MP4 compatible con iPhone."
        case .network: return "No se pudo conectar. Revisa tu conexión y la dirección del servidor."
        case .storage: return "No se pudo guardar la cuenta de forma segura en este dispositivo."
        }
    }
}

public enum Endpoint {
    public static func server(_ raw: String, playlist: Bool = false) throws -> URL {
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard var c = URLComponents(string: value), c.host?.isEmpty == false,
              c.user == nil, c.password == nil, c.fragment == nil else { throw PimflexError.invalidServer }
        guard c.scheme?.lowercased() == "https" else { throw PimflexError.insecureURL }
        if !playlist {
            guard c.query == nil else { throw PimflexError.invalidServer }
            c.path = c.path.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
            c.path = c.path.isEmpty ? "" : "/" + c.path
        }
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
    public static func api(_ account: Account, action: String? = nil, extra: [URLQueryItem] = []) throws -> URL {
        guard account.mode == .xtream else { throw PimflexError.invalidServer }
        var c = URLComponents(url: account.server.appendingPathComponent("player_api.php"), resolvingAgainstBaseURL: false)!
        c.queryItems = [URLQueryItem(name: "username", value: account.username), URLQueryItem(name: "password", value: account.password)]
        if let action { c.queryItems?.append(URLQueryItem(name: "action", value: action)) }
        c.queryItems?.append(contentsOf: extra)
        // PHP query decoding treats a literal '+' as a space.
        c.percentEncodedQuery = c.percentEncodedQuery?.replacingOccurrences(of: "+", with: "%2B")
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
    public static func playback(_ account: Account, item: MediaItem) throws -> URL {
        if let direct = item.directURL {
            guard direct.scheme?.lowercased() == "https" else { throw PimflexError.insecureURL }
            if ["mkv", "avi", "flv", "wmv"].contains(direct.pathExtension.lowercased()) { throw PimflexError.unsupportedFormat }
            return direct
        }
        guard !item.providerID.isEmpty, item.providerID.allSatisfy({ $0.isASCII && $0.isNumber }) else { throw PimflexError.invalidResponse }
        let ext = item.kind == .live ? "m3u8" : item.fileExtension.lowercased()
        guard ["m3u8", "mp4", "m4v", "mov", "mp3", "m4a", "aac"].contains(ext) else { throw PimflexError.unsupportedFormat }
        let allowed = CharacterSet.alphanumerics.union(CharacterSet(charactersIn: "-._~"))
        let path = [item.kind.rawValue, account.username, account.password, item.providerID + "." + ext]
            .map { $0.addingPercentEncoding(withAllowedCharacters: allowed)! }.joined(separator: "/")
        var c = URLComponents(url: account.server, resolvingAgainstBaseURL: false)!
        let prefix = c.percentEncodedPath.trimmingCharacters(in: CharacterSet(charactersIn: "/"))
        c.percentEncodedPath = "/" + (prefix.isEmpty ? "" : prefix + "/") + path
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
}
