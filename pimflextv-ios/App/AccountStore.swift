import Foundation
import Combine
import Security
import PimflexCore

enum AccountStore {
    static func save(_ account: Account) throws { try AccountLibrary.activate(account) }
    static func load() -> Account? { AccountLibrary.current() }
    static func delete() throws { try AccountLibrary.deactivate() }
}

@MainActor
final class AppModel: ObservableObject {
    let api = APIClient()
    @Published private(set) var account: Account?
    @Published private(set) var savedAccounts: [Account] = []
    @Published var connecting = false
    @Published var error: String?
    @Published var expiration = ""
    @Published private(set) var playlist: [MediaItem] = []
    @Published private(set) var favorites: Set<String> = []
    @Published private(set) var positions: [String: Double] = [:]
    @Published private(set) var lastUpdated: [MediaKind: Date] = [:]
    private var generation = UUID()
    private var catalogCache: [MediaKind: ([PimflexCore.Category], [MediaItem])] = [:]
    #if DEBUG
    private(set) var usesTestFixtures = false
    #else
    var usesTestFixtures: Bool { false }
    #endif

    init() {
        #if DEBUG
        if ProcessInfo.processInfo.arguments.contains("--ui-testing") {
            usesTestFixtures = true
            if ProcessInfo.processInfo.arguments.contains("--preview-account") {
                account = Account(mode: .xtream, server: URL(string: "https://example.com")!, username: "Vista previa", password: "fixture-only")
                expiration = String(Date().addingTimeInterval(86_400 * 30).timeIntervalSince1970)
                savedAccounts = [account!, Account(mode: .xtream, server: URL(string: "https://example.com")!, username: "Otra vista previa", password: "fixture-only")]
            }
            return
        }
        #endif
        account = AccountStore.load(); savedAccounts = AccountLibrary.accounts(); loadPreferences()
    }
    func connect(mode: SourceMode, server: String, username: String, password: String, allowingInsecureHTTP: Bool = false) async {
        guard !connecting else { return }
        let requestGeneration = UUID(); generation = requestGeneration
        connecting = true; error = nil
        defer { if generation == requestGeneration { connecting = false } }
        do {
            let url = try Endpoint.server(server, playlist: mode == .m3u, allowingInsecureHTTP: allowingInsecureHTTP)
            if mode == .xtream && (username.trimmingCharacters(in: .whitespaces).isEmpty || password.isEmpty) { throw PimflexError.invalidCredentials }
            let candidate = Account(mode: mode, server: url, username: username.trimmingCharacters(in: .whitespacesAndNewlines), password: password, allowingInsecureHTTP: allowingInsecureHTTP)
            var entries: [MediaItem] = []; var expires = ""
            #if DEBUG
            if usesTestFixtures { expires = String(Date().addingTimeInterval(86_400 * 30).timeIntervalSince1970) }
            else if mode == .xtream { expires = try await api.authenticate(candidate) }
            else { entries = try await api.playlist(candidate) }
            #else
            if mode == .xtream { expires = try await api.authenticate(candidate) }
            else { entries = try await api.playlist(candidate) }
            #endif
            try Task.checkCancellation()
            guard generation == requestGeneration else { return }
            if !usesTestFixtures { try AccountStore.save(candidate); savedAccounts = AccountLibrary.accounts() }
            catalogCache = [:]; lastUpdated = [:]
            account = candidate; playlist = entries; expiration = expires; favorites = []; positions = [:]; loadPreferences()
        } catch is CancellationError { }
        catch { if generation == requestGeneration { self.error = message(error) } }
    }
    func restore() async {
        guard let account else { return }
        if usesTestFixtures { return }
        let requestGeneration = generation
        do {
            let entries: [MediaItem]
            let expires: String
            if account.mode == .m3u { entries = try await api.playlist(account); expires = "" }
            else { entries = []; expires = try await api.authenticate(account) }
            try Task.checkCancellation()
            guard generation == requestGeneration, self.account == account else { return }
            playlist = entries; expiration = expires; error = nil
            if account.mode == .m3u { catalogCache = [:]; lastUpdated = [:] }
        } catch is CancellationError { }
        catch { if generation == requestGeneration, self.account == account { self.error = message(error) } }
    }
    func catalog(_ kind: MediaKind, refresh: Bool = false) async throws -> ([PimflexCore.Category], [MediaItem]) {
        guard let account else { throw CancellationError() }
        #if DEBUG
        if usesTestFixtures { return Self.fixtureCatalog(kind) }
        #endif
        if !refresh, let cached = catalogCache[kind] { return cached }
        let requestGeneration = generation
        let result: ([PimflexCore.Category], [MediaItem])
        var refreshedPlaylist: [MediaItem]?
        if account.mode == .m3u {
            let entries: [MediaItem]
            if refresh || playlist.isEmpty { entries = try await api.playlist(account); refreshedPlaylist = entries }
            else { entries = playlist }
            let filtered = entries.filter { $0.kind == kind }
            let groups = Set(filtered.map(\.categoryID)).filter { !$0.isEmpty }.sorted().map { PimflexCore.Category(id: $0, name: $0) }
            result = (groups, filtered)
        } else {
            async let groups = api.categories(account, kind: kind)
            async let entries = api.catalog(account, kind: kind)
            result = try await (groups, entries)
        }
        try Task.checkCancellation()
        guard generation == requestGeneration, self.account == account else { throw CancellationError() }
        if let refreshedPlaylist { playlist = refreshedPlaylist; catalogCache = [:]; lastUpdated = [:] }
        catalogCache[kind] = result; lastUpdated[kind] = Date()
        return result
    }
    func refreshCatalogs() async {
        await restore()
        guard error == nil, let account else { return }
        let requestGeneration = generation
        do {
            for kind in MediaKind.allCases {
                _ = try await catalog(kind, refresh: account.mode == .xtream)
            }
        } catch is CancellationError { }
        catch { if generation == requestGeneration, self.account == account { self.error = message(error) } }
    }
    func removeAccount(_ saved: Account) {
        do {
            if !usesTestFixtures { try AccountLibrary.remove(storageID: saved.storageID) }
            // A pending connect must not re-save an account after its removal.
            generation = UUID(); connecting = false
            savedAccounts.removeAll { $0.storageID == saved.storageID }
            if account?.storageID == saved.storageID {
                account = nil; playlist = []; expiration = ""; favorites = []; positions = [:]
                catalogCache = [:]; lastUpdated = [:]
            }
            error = nil
        } catch { self.error = message(error) }
    }
    func signOut() {
        do {
            if !usesTestFixtures { try AccountStore.delete() }
            generation = UUID(); connecting = false
            account = nil; playlist = []; expiration = ""; favorites = []; positions = [:]
            catalogCache = [:]; lastUpdated = [:]; error = nil
        } catch { self.error = message(error) }
    }
    #if DEBUG
    static func fixtureCatalog(_ kind: MediaKind) -> ([PimflexCore.Category], [MediaItem]) {
        let names: [String]
        switch kind {
        case .live: names = ["Canal de muestra", "Noticias de muestra", "Deportes de muestra"]
        case .movie: names = ["Película de muestra", "Aventura de muestra", "Documental de muestra"]
        case .series: names = ["Serie de muestra", "Historias de muestra", "Naturaleza de muestra"]
        }
        return ([PimflexCore.Category(id: "sample", name: "Muestra"), PimflexCore.Category(id: "extra", name: "Más títulos")], names.enumerated().map {
            MediaItem(providerID: String($0.offset + 1), name: $0.element, kind: kind, categoryID: $0.offset == 2 ? "extra" : "sample")
        })
    }
    #endif
    func toggleFavorite(_ item: MediaItem) {
        if favorites.contains(item.id) { favorites.remove(item.id) } else { favorites.insert(item.id) }
        guard let account, !usesTestFixtures else { return }
        UserDefaults.standard.set(Array(favorites), forKey: "favorites.\(account.storageID)")
    }
    func savePosition(_ seconds: Double, item: MediaItem) {
        guard item.kind != .live, seconds.isFinite, seconds >= 0, let account, !usesTestFixtures else { return }
        positions[item.id] = seconds
        UserDefaults.standard.set(positions, forKey: "positions.\(account.storageID)")
    }
    func resetPreferences() {
        guard let account else { return }
        favorites = []; positions = [:]
        guard !usesTestFixtures else { return }
        UserDefaults.standard.removeObject(forKey: "favorites.\(account.storageID)")
        UserDefaults.standard.removeObject(forKey: "positions.\(account.storageID)")
    }
    private func loadPreferences() {
        guard let account, !usesTestFixtures else { return }
        favorites = Set(UserDefaults.standard.stringArray(forKey: "favorites.\(account.storageID)") ?? [])
        positions = UserDefaults.standard.dictionary(forKey: "positions.\(account.storageID)") as? [String: Double] ?? [:]
    }
    func message(_ error: Error) -> String { (error as? PimflexError)?.errorDescription ?? "No se pudo completar la operación. Inténtalo de nuevo." }
}
