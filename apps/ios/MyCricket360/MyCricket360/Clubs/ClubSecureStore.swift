import Foundation
import Security

/// Keychain wrapper for auth token and last selected club.
enum ClubSecureStore {
    private static let service = "org.mycricket360.app"

    static func set(_ value: String, forKey key: String) {
        let data = Data(value.utf8)
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
        var add = query
        add[kSecValueData as String] = data
        add[kSecAttrAccessible as String] = kSecAttrAccessibleAfterFirstUnlock
        SecItemAdd(add as CFDictionary, nil)
    }

    static func string(forKey key: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
            kSecReturnData as String: true,
            kSecMatchLimit as String: kSecMatchLimitOne,
        ]
        var item: CFTypeRef?
        let status = SecItemCopyMatching(query as CFDictionary, &item)
        guard status == errSecSuccess, let data = item as? Data else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func remove(_ key: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: key,
        ]
        SecItemDelete(query as CFDictionary)
    }
}

enum AuthTokenStore {
    private static let accessKey = "mc360.accessToken"
    private static let refreshKey = "mc360.refreshToken"

    static func save(_ token: String) {
        ClubSecureStore.set(token, forKey: accessKey)
    }

    static func load() -> String? {
        ClubSecureStore.string(forKey: accessKey)
    }

    static func saveRefresh(_ token: String) {
        ClubSecureStore.set(token, forKey: refreshKey)
    }

    static func loadRefresh() -> String? {
        ClubSecureStore.string(forKey: refreshKey)
    }

    static func clear() {
        ClubSecureStore.remove(accessKey)
        ClubSecureStore.remove(refreshKey)
    }
}
