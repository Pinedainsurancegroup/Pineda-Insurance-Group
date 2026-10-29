import Foundation

// Do not forward account query parameters to a different origin via redirects.
public final class SafeRedirects: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    public static func permits(from: URL, to: URL) -> Bool {
        to.scheme == "https" && to.user == nil && to.password == nil && from.host?.lowercased() == to.host?.lowercased() && (from.port ?? 443) == (to.port ?? 443)
    }
    public func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                           newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        guard let original = task.originalRequest?.url, let next = request.url, Self.permits(from: original, to: next) else {
            completionHandler(nil); return
        }
        completionHandler(request)
    }
}

public actor APIClient {
    private let session: URLSession
    public init(session: URLSession? = nil) {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 25; config.timeoutIntervalForResource = 60
        config.urlCache = nil; config.httpCookieStorage = nil; config.httpShouldSetCookies = false
        self.session = session ?? URLSession(configuration: config, delegate: SafeRedirects(), delegateQueue: nil)
    }
    public func data(from url: URL) async throws -> Data {
        guard url.scheme == "https" else { throw PimflexError.insecureURL }
        do {
            var request = URLRequest(url: url); request.setValue("PIMFLEXTV-iOS/0.1", forHTTPHeaderField: "User-Agent")
            let (bytes, response) = try await session.bytes(for: request)
            guard let http = response as? HTTPURLResponse else { throw PimflexError.invalidResponse }
            if http.statusCode == 401 || http.statusCode == 403 { throw PimflexError.invalidCredentials }
            guard (200..<300).contains(http.statusCode) else { throw PimflexError.invalidResponse }
            let maximum = 32 * 1024 * 1024
            guard response.expectedContentLength <= Int64(maximum) else { throw PimflexError.invalidResponse }
            var data = Data()
            for try await byte in bytes { if data.count >= maximum { throw PimflexError.invalidResponse }; data.append(byte) }
            return data
        } catch is CancellationError { throw CancellationError() }
        catch let error as PimflexError { throw error }
        catch { if Task.isCancelled { throw CancellationError() }; throw PimflexError.network }
    }
    public func authenticate(_ account: Account) async throws -> String {
        try CatalogParser.authenticate(await data(from: Endpoint.api(account)))
    }
    public func categories(_ account: Account, kind: MediaKind) async throws -> [Category] {
        try CatalogParser.categories(await data(from: Endpoint.api(account, action: kind.categoryAction)))
    }
    public func catalog(_ account: Account, kind: MediaKind, category: String? = nil) async throws -> [MediaItem] {
        let extra = category.map { [URLQueryItem(name: "category_id", value: $0)] } ?? []
        return try CatalogParser.items(await data(from: Endpoint.api(account, action: kind.catalogAction, extra: extra)), kind: kind)
    }
    public func episodes(_ account: Account, seriesID: String) async throws -> [MediaItem] {
        try CatalogParser.episodes(await data(from: Endpoint.api(account, action: "get_series_info", extra: [URLQueryItem(name: "series_id", value: seriesID)])))
    }
    public func guide(_ account: Account, streamID: String) async throws -> [Programme] {
        try EPGParser.parse(await data(from: Endpoint.api(account, action: "get_short_epg", extra: [URLQueryItem(name: "stream_id", value: streamID), URLQueryItem(name: "limit", value: "20")])))
    }
    public func playlist(_ account: Account) async throws -> [MediaItem] {
        let data = try await data(from: account.server)
        guard let text = String(data: data, encoding: .utf8) else { throw PimflexError.invalidResponse }
        return try M3UParser.parse(text, baseURL: account.server)
    }
}
