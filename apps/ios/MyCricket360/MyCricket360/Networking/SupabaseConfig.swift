import Foundation

/// Public Supabase configuration for project **mycricket360** (org: personalyogesh).
/// Only URL + publishable/anon key. Never embed secret/service_role or database passwords.
enum SupabaseConfig {
    static var url: URL? {
        guard let raw = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_URL") as? String,
              !raw.isEmpty,
              !raw.contains("YOUR_PROJECT_REF"),
              let url = URL(string: raw)
        else { return nil }
        return url
    }

    /// Prefer SUPABASE_PUBLISHABLE_KEY; fall back to legacy SUPABASE_ANON_KEY.
    static var publishableKey: String? {
        let candidates = [
            Bundle.main.object(forInfoDictionaryKey: "SUPABASE_PUBLISHABLE_KEY") as? String,
            Bundle.main.object(forInfoDictionaryKey: "SUPABASE_ANON_KEY") as? String,
        ]
        for raw in candidates {
            guard let key = raw?.trimmingCharacters(in: .whitespacesAndNewlines),
                  !key.isEmpty,
                  !key.hasPrefix("YOUR_"),
                  !key.lowercased().hasPrefix("sb_secret_"),
                  !key.lowercased().contains("service_role")
            else { continue }
            return key
        }
        return nil
    }

    /// Back-compat alias used by auth client.
    static var anonKey: String? { publishableKey }

    static var isConfigured: Bool { url != nil && publishableKey != nil }

    /// Dashboard project label — not the Postgres database name.
    static let projectName = "mycricket360"
    static let organizationSlug = "personalyogesh"
}
