import Foundation

/// Minimal GoTrue password sign-in using the **publishable** anon key only.
struct SupabaseSessionDTO: Decodable {
    let access_token: String
    let token_type: String?
    let expires_in: Int?
    let refresh_token: String?
}

enum SupabaseAuthClient {
    static func signIn(email: String, password: String) async throws -> SupabaseSessionDTO {
        guard let base = SupabaseConfig.url, let anon = SupabaseConfig.anonKey else {
            throw APIClientError.http(503, "Supabase is not configured in Info.plist")
        }
        var request = URLRequest(url: base.appendingPathComponent("auth/v1/token"))
        var components = URLComponents(url: request.url!, resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "grant_type", value: "password")]
        request.url = components.url
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(anon, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(anon)", forHTTPHeaderField: "Authorization")
        struct Body: Encodable { let email: String; let password: String }
        request.httpBody = try JSONEncoder().encode(Body(email: email, password: password))
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            throw APIClientError.http(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
        return try JSONDecoder().decode(SupabaseSessionDTO.self, from: data)
    }
}
