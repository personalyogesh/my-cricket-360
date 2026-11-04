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

    static func signUp(email: String, password: String, displayName: String) async throws -> SupabaseSessionDTO? {
        guard let base = SupabaseConfig.url, let anon = SupabaseConfig.anonKey else {
            throw APIClientError.http(503, "Supabase is not configured in Info.plist")
        }
        var request = URLRequest(url: base.appendingPathComponent("auth/v1/signup"))
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(anon, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(anon)", forHTTPHeaderField: "Authorization")
        struct Body: Encodable {
            let email: String
            let password: String
            let data: [String: String]
        }
        request.httpBody = try JSONEncoder().encode(
            Body(email: email, password: password, data: ["display_name": displayName])
        )
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            throw APIClientError.http(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
        return try decodeSession(data)
    }

    static func refresh(refreshToken: String) async throws -> SupabaseSessionDTO {
        guard let base = SupabaseConfig.url, let anon = SupabaseConfig.anonKey else {
            throw APIClientError.http(503, "Supabase is not configured in Info.plist")
        }
        var components = URLComponents(url: base.appendingPathComponent("auth/v1/token"), resolvingAgainstBaseURL: false)!
        components.queryItems = [URLQueryItem(name: "grant_type", value: "refresh_token")]
        var request = URLRequest(url: components.url!)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue(anon, forHTTPHeaderField: "apikey")
        request.setValue("Bearer \(anon)", forHTTPHeaderField: "Authorization")
        struct Body: Encodable { let refresh_token: String }
        request.httpBody = try JSONEncoder().encode(Body(refresh_token: refreshToken))
        let (data, response) = try await URLSession.shared.data(for: request)
        guard let http = response as? HTTPURLResponse else { throw APIClientError.invalidResponse }
        guard (200..<300).contains(http.statusCode) else {
            throw APIClientError.http(http.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
        guard let session = try decodeSession(data) else {
            throw APIClientError.http(http.statusCode, "Supabase refresh did not return a session")
        }
        return session
    }

    private static func decodeSession(_ data: Data) throws -> SupabaseSessionDTO? {
        if let direct = try? JSONDecoder().decode(SupabaseSessionDTO.self, from: data),
           !direct.access_token.isEmpty {
            return direct
        }
        struct Envelope: Decodable {
            let access_token: String?
            let refresh_token: String?
            let expires_in: Int?
            let session: SupabaseSessionDTO?
        }
        let envelope = try JSONDecoder().decode(Envelope.self, from: data)
        if let session = envelope.session { return session }
        if let access = envelope.access_token {
            return SupabaseSessionDTO(
                access_token: access,
                token_type: "bearer",
                expires_in: envelope.expires_in,
                refresh_token: envelope.refresh_token
            )
        }
        return nil
    }
}
