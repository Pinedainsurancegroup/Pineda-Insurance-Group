import Foundation

// Do not forward account query parameters to a different origin via redirects.
public final class SafeRedirects: NSObject, URLSessionTaskDelegate, @unchecked Sendable {
    private let allowingInsecureHTTP: Bool
    public init(allowingInsecureHTTP: Bool = false) {
        self.allowingInsecureHTTP = allowingInsecureHTTP
        super.init()
    }
    public static func permits(from: URL, to: URL, allowingInsecureHTTP: Bool = false) -> Bool {
        guard let original = try? Endpoint.server(from.absoluteString, playlist: true, allowingInsecureHTTP: allowingInsecureHTTP),
              let next = try? Endpoint.server(to.absoluteString, playlist: true, allowingInsecureHTTP: allowingInsecureHTTP),
              original.scheme == next.scheme,
              original.host?.lowercased() == next.host?.lowercased() else { return false }
        let defaultPort = original.scheme == "https" ? 443 : 80
        return (original.port ?? defaultPort) == (next.port ?? defaultPort)
    }
    public func urlSession(_ session: URLSession, task: URLSessionTask, willPerformHTTPRedirection response: HTTPURLResponse,
                           newRequest request: URLRequest, completionHandler: @escaping (URLRequest?) -> Void) {
        guard let original = task.originalRequest?.url, let next = request.url,
              Self.permits(from: original, to: next, allowingInsecureHTTP: allowingInsecureHTTP) else {
            completionHandler(nil); return
        }
        completionHandler(request)
    }
}

public actor APIClient {
    private let session: URLSession
    private let compatibilitySession: URLSession
    public init(session: URLSession? = nil) {
        let config = URLSessionConfiguration.ephemeral
        config.timeoutIntervalForRequest = 25; config.timeoutIntervalForResource = 60
        config.urlCache = nil; config.httpCookieStorage = nil; config.httpShouldSetCookies = false
        self.session = session ?? URLSession(configuration: config, delegate: SafeRedirects(), delegateQueue: nil)
        // No authentication-challenge override: HTTPS certificate validation stays
        // with URLSession. The second session only changes the scoped redirect policy.
        self.compatibilitySession = session ?? URLSession(configuration: config, delegate: SafeRedirects(allowingInsecureHTTP: true), delegateQueue: nil)
    }
    public func data(from url: URL, allowingInsecureHTTP: Bool = false) async throws -> Data {
        try await resource(from: url, allowingInsecureHTTP: allowingInsecureHTTP).data
    }
    private func resource(from url: URL, allowingInsecureHTTP: Bool = false) async throws -> (data: Data, url: URL) {
        let url = try Endpoint.server(url.absoluteString, playlist: true, allowingInsecureHTTP: allowingInsecureHTTP)
        do {
            var request = URLRequest(url: url); request.setValue("PIMFLEXTV-iOS/0.1", forHTTPHeaderField: "User-Agent")
            let transport = allowingInsecureHTTP ? compatibilitySession : session
            let (bytes, response) = try await transport.bytes(for: request)
            guard let http = response as? HTTPURLResponse else { throw PimflexError.invalidResponse }
            guard let finalURL = response.url,
                  SafeRedirects.permits(from: url, to: finalURL, allowingInsecureHTTP: allowingInsecureHTTP) else { throw PimflexError.invalidResponse }
            if http.statusCode == 401 || http.statusCode == 403 { throw PimflexError.invalidCredentials }
            guard (200..<300).contains(http.statusCode) else { throw PimflexError.invalidResponse }
            let maximum = 32 * 1024 * 1024
            guard response.expectedContentLength <= Int64(maximum) else { throw PimflexError.invalidResponse }
            var data = Data()
            for try await byte in bytes { if data.count >= maximum { throw PimflexError.invalidResponse }; data.append(byte) }
            try Task.checkCancellation()
            return (data, finalURL)
        } catch is CancellationError { throw CancellationError() }
        catch let error as PimflexError { throw error }
        catch { if Task.isCancelled { throw CancellationError() }; throw PimflexError.network }
    }
    public func authenticate(_ account: Account) async throws -> String {
        try CatalogParser.authenticate(await data(from: Endpoint.api(account), allowingInsecureHTTP: account.insecureHTTPEnabled))
    }
    public func categories(_ account: Account, kind: MediaKind) async throws -> [Category] {
        try CatalogParser.categories(await data(from: Endpoint.api(account, action: kind.categoryAction), allowingInsecureHTTP: account.insecureHTTPEnabled))
    }
    public func catalog(_ account: Account, kind: MediaKind, category: String? = nil) async throws -> [MediaItem] {
        let extra = category.map { [URLQueryItem(name: "category_id", value: $0)] } ?? []
        return try CatalogParser.items(await data(from: Endpoint.api(account, action: kind.catalogAction, extra: extra), allowingInsecureHTTP: account.insecureHTTPEnabled), kind: kind, allowingInsecureHTTP: account.insecureHTTPEnabled)
    }
    public func episodes(_ account: Account, seriesID: String) async throws -> [MediaItem] {
        try CatalogParser.episodes(await data(from: Endpoint.api(account, action: "get_series_info", extra: [URLQueryItem(name: "series_id", value: seriesID)]), allowingInsecureHTTP: account.insecureHTTPEnabled), allowingInsecureHTTP: account.insecureHTTPEnabled)
    }
    public func guide(_ account: Account, streamID: String) async throws -> [Programme] {
        try EPGParser.parse(await data(from: Endpoint.api(account, action: "get_short_epg", extra: [URLQueryItem(name: "stream_id", value: streamID), URLQueryItem(name: "limit", value: "20")]), allowingInsecureHTTP: account.insecureHTTPEnabled))
    }
    public func playlist(_ account: Account) async throws -> [MediaItem] {
        let result = try await resource(from: account.server, allowingInsecureHTTP: account.insecureHTTPEnabled)
        guard let text = String(data: result.data, encoding: .utf8) else { throw PimflexError.invalidResponse }
        return try M3UParser.parse(text, baseURL: result.url, allowingInsecureHTTP: account.insecureHTTPEnabled)
    }
}
