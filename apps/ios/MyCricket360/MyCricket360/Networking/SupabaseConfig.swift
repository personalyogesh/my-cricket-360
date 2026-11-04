import Foundation

/// Public Supabase configuration for project **mycricket360** (org: personalyogesh).
/// Only URL + anon/publishable key. Never embed service-role or database passwords.
enum SupabaseConfig {
    static var url: URL? {
        guard let raw = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_URL") as? String,
              !raw.isEmpty,
              !raw.contains("YOUR_PROJECT_REF"),
              let url = URL(string: raw)
        else { return nil }
        return url
    }

    static var anonKey: String? {
        guard let key = Bundle.main.object(forInfoDictionaryKey: "SUPABASE_ANON_KEY") as? String,
              !key.isEmpty,
              !key.hasPrefix("YOUR_"),
              !key.lowercased().contains("service_role")
        else { return nil }
        return key
    }

    static var isConfigured: Bool { url != nil && anonKey != nil }

    /// Dashboard project label — not the Postgres database name.
    static let projectName = "mycricket360"
    static let organizationSlug = "personalyogesh"
}
