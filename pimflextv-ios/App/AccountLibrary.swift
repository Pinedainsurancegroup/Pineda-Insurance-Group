import Foundation
import Security
import PimflexCore

/// Keeps the selected account and saved playlists in one Keychain item.
enum AccountLibrary {
    private struct Vault: Codable {
        var currentID: String?
        var accounts: [Account]
    }

    private struct LoadedVault {
        let vault: Vault
        let requiresMigration: Bool
    }

    private static let service = "com.pimflextv.ios.account"
    private static let vaultKey = "vault-v1"
    private static let legacyKey = "current"
    private static let lock = NSLock()

    static func current() -> Account? {
        synchronized {
            guard let vault = readForDisplay(), let currentID = vault.currentID else { return nil }
            return vault.accounts.first { $0.storageID == currentID }
        }
    }

    static func accounts() -> [Account] {
        synchronized { readForDisplay()?.accounts ?? [] }
    }

    static func activate(_ account: Account) throws {
        try synchronized {
            var vault = try readVault().vault
            if let index = vault.accounts.firstIndex(where: { $0.storageID == account.storageID }) {
                vault.accounts[index] = account
            } else {
                vault.accounts.append(account)
            }
            vault.currentID = account.storageID
            try saveVault(vault)
        }
    }

    /// Signing out retains saved accounts and their independent preferences.
    static func deactivate() throws {
        try synchronized {
            var vault = try readVault().vault
            vault.currentID = nil
            try saveVault(vault)
        }
    }

    static func remove(storageID: String) throws {
        try synchronized {
            var vault = try readVault().vault
            vault.accounts.removeAll { $0.storageID == storageID }
            if vault.currentID == storageID { vault.currentID = nil }
            try saveVault(vault)
        }
    }

    private static func synchronized<T>(_ body: () throws -> T) rethrows -> T {
        lock.lock()
        defer { lock.unlock() }
        return try body()
    }

    private static func readForDisplay() -> Vault? {
        do {
            let loaded = try readVault()
            if loaded.requiresMigration {
                // A failed migration must not make the readable legacy account disappear.
                // saveVault leaves the legacy item intact unless the vault write succeeds.
                try? saveVault(loaded.vault)
            }
            return loaded.vault
        } catch {
            // The nonthrowing UI API has no account to present. Mutations never use
            // this fallback: they call readVault and propagate the storage error.
            return nil
        }
    }

    private static func readVault() throws -> LoadedVault {
        if let data = try readData(accountKey: vaultKey) {
            let vault: Vault
            do { vault = try JSONDecoder().decode(Vault.self, from: data) }
            catch { throw PimflexError.storage }
            try validate(vault)
            return LoadedVault(vault: vault, requiresMigration: false)
        }

        // Only an absent vault permits migration; read/decode failures must not
        // fall back to an empty list or overwrite an existing vault.
        if let data = try readData(accountKey: legacyKey) {
            let account: Account
            do { account = try JSONDecoder().decode(Account.self, from: data) }
            catch { throw PimflexError.storage }
            return LoadedVault(
                vault: Vault(currentID: account.storageID, accounts: [account]),
                requiresMigration: true
            )
        }
        return LoadedVault(vault: Vault(currentID: nil, accounts: []), requiresMigration: false)
    }

    private static func validate(_ vault: Vault) throws {
        let ids = Set(vault.accounts.map(\.storageID))
        guard ids.count == vault.accounts.count else { throw PimflexError.storage }
        if let currentID = vault.currentID, !ids.contains(currentID) {
            throw PimflexError.storage
        }
    }

    private static func query(accountKey: String) -> [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: accountKey]
    }

    private static func readData(accountKey: String) throws -> Data? {
        var request = query(accountKey: accountKey)
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var item: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &item)
        switch status {
        case errSecSuccess:
            guard let data = item as? Data else { throw PimflexError.storage }
            return data
        case errSecItemNotFound:
            return nil
        default:
            throw PimflexError.storage
        }
    }

    private static func saveVault(_ vault: Vault) throws {
        try validate(vault)
        let data: Data
        do { data = try JSONEncoder().encode(vault) }
        catch { throw PimflexError.storage }
        let changes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlockThisDeviceOnly
        ]
        let request = query(accountKey: vaultKey)
        let status = SecItemUpdate(request as CFDictionary, changes as CFDictionary)
        if status == errSecItemNotFound {
            var insert = request
            changes.forEach { insert[$0.key] = $0.value }
            guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else {
                throw PimflexError.storage
            }
        } else if status != errSecSuccess {
            throw PimflexError.storage
        }

        // This happens only after the complete active-account/list state is saved.
        // Keep an empty vault after sign-out/removal so a leftover legacy item
        // cannot reactivate an account if this best-effort deletion fails.
        _ = SecItemDelete(query(accountKey: legacyKey) as CFDictionary)
    }
}
