import Foundation
import Combine
import Security
import PimflexCore

enum AccountStore {
    private static var query: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: "com.pimflextv.ios.account",
         kSecAttrAccount as String: "current"]
    }
    static func save(_ account: Account) throws {
        let data = try JSONEncoder().encode(account)
        let changes: [String: Any] = [kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly]
        let status = SecItemUpdate(query as CFDictionary, changes as CFDictionary)
        if status == errSecItemNotFound {
            var insert = query; changes.forEach { insert[$0.key] = $0.value }
            guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else { throw PimflexError.storage }
        } else if status != errSecSuccess { throw PimflexError.storage }
    }
    static func load() -> Account? {
        var q = query; q[kSecReturnData as String] = true; q[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        guard SecItemCopyMatching(q as CFDictionary, &item) == errSecSuccess, let data = item as? Data else { return nil }
        return try? JSONDecoder().decode(Account.self, from: data)
    }
    static func delete() throws {
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else { throw PimflexError.storage }
    }
}

@MainActor
final class AppModel: ObservableObject {
    let api = APIClient()
    @Published private(set) var account: Account?
    @Published var connecting = false
    @Published var error: String?
    @Published var expiration = ""
    @Published private(set) var playlist: [MediaItem] = []
    @Published private(set) var favorites: Set<String> = []
    @Published private(set) var positions: [String: Double] = [:]

    init() { account = AccountStore.load(); loadPreferences() }
    func connect(mode: SourceMode, server: String, username: String, password: String) async {
        guard !connecting else { return }
        connecting = true; error = nil
        defer { connecting = false }
        do {
            let url = try Endpoint.server(server, playlist: mode == .m3u)
            if mode == .xtream && (username.trimmingCharacters(in: .whitespaces).isEmpty || password.isEmpty) { throw PimflexError.invalidCredentials }
            let candidate = Account(mode: mode, server: url, username: username.trimmingCharacters(in: .whitespacesAndNewlines), password: password)
            var entries: [MediaItem] = []; var expires = ""
            if mode == .xtream { expires = try await api.authenticate(candidate) }
            else { entries = try await api.playlist(candidate) }
            try Task.checkCancellation()
            try AccountStore.save(candidate)
            account = candidate; playlist = entries; expiration = expires; loadPreferences()
        } catch is CancellationError { }
        catch { self.error = message(error) }
    }
    func restore() async {
        guard let account else { return }
        do {
            if account.mode == .m3u { playlist = try await api.playlist(account) }
            else { expiration = try await api.authenticate(account) }
        } catch is CancellationError { }
        catch { self.error = message(error) }
    }
    func signOut() {
        do { try AccountStore.delete(); account = nil; playlist = []; expiration = ""; favorites = []; positions = [:]; error = nil }
        catch { self.error = message(error) }
    }
    func toggleFavorite(_ item: MediaItem) {
        if favorites.contains(item.id) { favorites.remove(item.id) } else { favorites.insert(item.id) }
        guard let account else { return }
        UserDefaults.standard.set(Array(favorites), forKey: "favorites.\(account.storageID)")
    }
    func savePosition(_ seconds: Double, item: MediaItem) {
        guard item.kind != .live, seconds.isFinite, seconds >= 0, let account else { return }
        positions[item.id] = seconds
        UserDefaults.standard.set(positions, forKey: "positions.\(account.storageID)")
    }
    func resetPreferences() {
        guard let account else { return }
        favorites = []; positions = [:]
        UserDefaults.standard.removeObject(forKey: "favorites.\(account.storageID)")
        UserDefaults.standard.removeObject(forKey: "positions.\(account.storageID)")
    }
    private func loadPreferences() {
        guard let account else { return }
        favorites = Set(UserDefaults.standard.stringArray(forKey: "favorites.\(account.storageID)") ?? [])
        positions = UserDefaults.standard.dictionary(forKey: "positions.\(account.storageID)") as? [String: Double] ?? [:]
    }
    func message(_ error: Error) -> String { (error as? PimflexError)?.errorDescription ?? "No se pudo completar la operación. Inténtalo de nuevo." }
}
