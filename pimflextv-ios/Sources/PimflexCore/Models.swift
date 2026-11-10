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
    // Optional for compatibility with accounts saved before the explicit opt-in.
    public let allowingInsecureHTTP: Bool?
    public var insecureHTTPEnabled: Bool { allowingInsecureHTTP == true }
    public init(mode: SourceMode, server: URL, username: String = "", password: String = "", allowingInsecureHTTP: Bool = false) {
        self.mode = mode; self.server = server; self.username = username; self.password = password
        self.allowingInsecureHTTP = allowingInsecureHTTP
    }
    // Namespaces history/favorites without persisting credentials in preferences.
    public var storageID: String {
        SHA256.hash(data: Data("\(mode.rawValue)|\(server.absoluteString)|\(username)".utf8))
            .map { String(format: "%02x", $0) }.joined()
    }
}

public enum PimflexError: Error, LocalizedError, Equatable {
    case invalidServer, insecureURL, unsupportedHTTPHost, invalidCredentials, inactiveAccount, invalidResponse, playlistTooLarge, emptyPlaylist, unsupportedFormat, network, storage
    public var errorDescription: String? {
        switch self {
        case .invalidServer: return "Revisa la dirección de tu servidor."
        case .insecureURL: return "Activa «Mi servidor requiere HTTP» para usar esta dirección HTTP, o utiliza una dirección HTTPS."
        case .unsupportedHTTPHost: return "Esta app no admite HTTP para esa dirección. Usa HTTPS o revisa la dirección de tu servidor."
        case .invalidCredentials: return "El servidor no aceptó el usuario o la contraseña."
        case .inactiveAccount: return "Tu cuenta no está activa. Contacta a tu proveedor."
        case .invalidResponse: return "El servidor devolvió una respuesta que no pudimos leer."
        case .playlistTooLarge: return "Esta lista es demasiado grande. Usa el acceso por usuario y contraseña o pide una lista más pequeña a tu proveedor."
        case .emptyPlaylist: return "La lista no contiene transmisiones compatibles con esta conexión."
        case .unsupportedFormat: return "Este formato requiere otro motor de video. Pide a tu proveedor una versión HLS o MP4 compatible con iPhone."
        case .network: return "No se pudo conectar. Revisa tu conexión y la dirección del servidor."
        case .storage: return "No se pudo guardar la cuenta de forma segura en este dispositivo."
        }
    }
}

public enum Endpoint {
    public static let approvedInsecureHTTPHosts: Set<String> = ["moonspelltools.cc", "my-vionex.com"]

    public static func loginAccount(mode: SourceMode, server raw: String, username: String = "", password: String = "", allowingInsecureHTTP: Bool = false) throws -> Account {
        let url = try server(raw, playlist: mode == .m3u, allowingInsecureHTTP: allowingInsecureHTTP)
        if mode == .m3u, let credentials = providerPlaylistCredentials(url) {
            // These known providers expose their complete catalog (including every
            // episode) in get.php. Import the same account via their API instead of
            // downloading that very large file just to sign in. Keep secrets in the
            // existing Keychain account fields, never in the saved server address.
            return Account(mode: .xtream, server: try server(url.absoluteString, allowingInsecureHTTP: allowingInsecureHTTP),
                           username: credentials.username, password: credentials.password, allowingInsecureHTTP: allowingInsecureHTTP)
        }
        let name = username.trimmingCharacters(in: .whitespacesAndNewlines)
        if mode == .xtream && (name.isEmpty || password.isEmpty) { throw PimflexError.invalidCredentials }
        return Account(mode: mode, server: url, username: name, password: password, allowingInsecureHTTP: allowingInsecureHTTP)
    }

    private static func providerPlaylistCredentials(_ url: URL) -> (username: String, password: String)? {
        guard let host = url.host?.lowercased(), approvedInsecureHTTPHosts.contains(host),
              url.lastPathComponent.lowercased() == "get.php",
              var components = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return nil }
        // Match PHP form decoding: a literal '+' means space, whereas '%2B'
        // is a plus in the actual credential. Do not decode values twice.
        components.percentEncodedQuery = components.percentEncodedQuery?.replacingOccurrences(of: "+", with: "%20")
        let items = components.queryItems ?? []
        let names: Set<String> = ["username", "password", "type", "output"]
        guard items.allSatisfy({ names.contains($0.name) }),
              Set(items.map(\.name)).count == items.count else { return nil }
        func value(_ name: String) -> String? { items.first(where: { $0.name == name })?.value }
        guard let username = value("username"), !username.isEmpty,
              let password = value("password"), !password.isEmpty,
              let type = value("type"), ["m3u", "m3u_plus"].contains(type.lowercased()) else { return nil }
        return (username, password)
    }

    public static func server(_ raw: String, playlist: Bool = false, allowingInsecureHTTP: Bool = false) throws -> URL {
        let value = raw.trimmingCharacters(in: .whitespacesAndNewlines)
        guard var c = URLComponents(string: value), let host = c.host, !host.isEmpty,
              c.user == nil, c.password == nil, c.fragment == nil else { throw PimflexError.invalidServer }
        let scheme = c.scheme?.lowercased()
        guard scheme == "https" || scheme == "http" else { throw PimflexError.invalidServer }
        let approvedHost = approvedInsecureHTTPHosts.contains(host.lowercased())
        if scheme == "http" && !approvedHost { throw PimflexError.unsupportedHTTPHost }
        let approvedHTTP = allowingInsecureHTTP && scheme == "http" && approvedHost
        guard scheme == "https" || approvedHTTP else { throw PimflexError.insecureURL }
        guard c.port.map({ (1...65535).contains($0) }) ?? true else { throw PimflexError.invalidServer }
        c.scheme = scheme
        if !playlist {
            // Users often paste a portal or playlist address instead of its base.
            // Remove only a known terminal route. Keep encoded slashes in tenant paths
            // and leave M3U query credentials untouched in playlist mode.
            var path = c.percentEncodedPath
            while path.hasSuffix("/") { path.removeLast() }
            let route = path.split(separator: "/", omittingEmptySubsequences: false).last?.lowercased() ?? ""
            if ["login.php", "player_api.php", "get.php"].contains(route) {
                path = String(path.dropLast(route.count))
                while path.hasSuffix("/") { path.removeLast() }
                c.query = nil // Xtream uses the separately entered credentials.
            } else if c.query != nil { throw PimflexError.invalidServer }
            c.percentEncodedPath = path
        }
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
    public static func api(_ account: Account, action: String? = nil, extra: [URLQueryItem] = []) throws -> URL {
        guard account.mode == .xtream else { throw PimflexError.invalidServer }
        let base = try server(account.server.absoluteString, allowingInsecureHTTP: account.insecureHTTPEnabled)
        guard var c = URLComponents(url: base, resolvingAgainstBaseURL: false) else { throw PimflexError.invalidServer }
        c.percentEncodedPath += "/player_api.php"
        c.queryItems = [URLQueryItem(name: "username", value: account.username), URLQueryItem(name: "password", value: account.password)]
        if let action { c.queryItems?.append(URLQueryItem(name: "action", value: action)) }
        c.queryItems?.append(contentsOf: extra)
        // PHP query decoding treats a literal '+' as a space.
        c.percentEncodedQuery = c.percentEncodedQuery?.replacingOccurrences(of: "+", with: "%2B")
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
    public static func playback(_ account: Account, item: MediaItem) throws -> URL {
        if let direct = item.directURL {
            let validated = try server(direct.absoluteString, playlist: true, allowingInsecureHTTP: account.insecureHTTPEnabled)
            if ["mkv", "avi", "flv", "wmv"].contains(validated.pathExtension.lowercased()) { throw PimflexError.unsupportedFormat }
            return validated
        }
        guard account.mode == .xtream else { throw PimflexError.invalidServer }
        guard !item.providerID.isEmpty, item.providerID.allSatisfy({ $0.isASCII && $0.isNumber }) else { throw PimflexError.invalidResponse }
        let ext = item.kind == .live ? "m3u8" : item.fileExtension.lowercased()
        guard ["m3u8", "mp4", "m4v", "mov", "mp3", "m4a", "aac"].contains(ext) else { throw PimflexError.unsupportedFormat }
        let allowed = CharacterSet(charactersIn: "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~")
        let path = [item.kind.rawValue, account.username, account.password, item.providerID + "." + ext]
            .map { $0.addingPercentEncoding(withAllowedCharacters: allowed)! }.joined(separator: "/")
        let base = try server(account.server.absoluteString, allowingInsecureHTTP: account.insecureHTTPEnabled)
        guard var c = URLComponents(url: base, resolvingAgainstBaseURL: false) else { throw PimflexError.invalidServer }
        c.percentEncodedPath += "/" + path
        guard let url = c.url else { throw PimflexError.invalidServer }; return url
    }
}
