import Foundation

enum APIClientError: LocalizedError {
    case invalidResponse
    case http(Int, String)
    case decoding(Error)

    var errorDescription: String? {
        switch self {
        case .invalidResponse: return "Invalid response"
        case let .http(code, body): return "HTTP \(code): \(body)"
        case let .decoding(error): return "Decoding failed: \(error.localizedDescription)"
        }
    }
}

private struct AnyEncodable: Encodable {
    private let encodeFunc: (Encoder) throws -> Void
    init(_ wrapped: any Encodable) {
        self.encodeFunc = wrapped.encode
    }
    func encode(to encoder: Encoder) throws {
        try encodeFunc(encoder)
    }
}

actor APIClient {
    static let shared = APIClient()

    private let session: URLSession
    private let decoder: JSONDecoder

    init(session: URLSession = .shared) {
        self.session = session
        self.decoder = JSONDecoder()
    }

    func request<T: Decodable>(
        _ method: String,
        path: String,
        token: String? = nil,
        body: (any Encodable)? = nil
    ) async throws -> T {
        let trimmed = path.hasPrefix("/") ? String(path.dropFirst()) : path
        guard let url = URL(string: trimmed, relativeTo: APIConfig.baseURL)?.absoluteURL else {
            throw APIClientError.invalidResponse
        }
        var request = URLRequest(url: url)
        request.httpMethod = method
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let token {
            request.setValue("Bearer \(token)", forHTTPHeaderField: "Authorization")
        }
        if let body {
            request.setValue("application/json", forHTTPHeaderField: "Content-Type")
            request.httpBody = try JSONEncoder().encode(AnyEncodable(body))
        }

        let (data, response) = try await session.data(for: request)
        guard let http = response as? HTTPURLResponse else {
            throw APIClientError.invalidResponse
        }
        guard (200..<300).contains(http.statusCode) else {
            let message = String(data: data, encoding: .utf8) ?? ""
            throw APIClientError.http(http.statusCode, message)
        }
        do {
            return try decoder.decode(T.self, from: data)
        } catch {
            throw APIClientError.decoding(error)
        }
    }

    func issueDevToken(email: String, displayName: String) async throws -> DevTokenResponseDTO {
        struct Body: Encodable {
            let email: String
            let display_name: String
        }
        return try await request(
            "POST",
            path: "/v1/auth/dev-token",
            body: Body(email: email, display_name: displayName)
        )
    }

    func me(token: String) async throws -> MeDTO {
        try await request("GET", path: "/v1/me", token: token)
    }

    func requestMembership(token: String, slug: String) async throws -> MembershipDTO {
        try await request(
            "POST",
            path: "/v1/me/memberships",
            token: token,
            body: MembershipRequestDTO(organization_slug: slug, role: "member")
        )
    }

    func publicSponsors(slug: String) async throws -> [SponsorDTO] {
        try await request("GET", path: "/v1/orgs/\(slug)/sponsors")
    }

    func publicTeams(slug: String) async throws -> [TeamDTO] {
        try await request("GET", path: "/v1/orgs/\(slug)/teams")
    }

    func publicFixtures(
        slug: String,
        when: String? = "upcoming",
        formatCode: String? = nil
    ) async throws -> FixturePageDTO {
        var parts = ["limit=50"]
        if let when, !when.isEmpty {
            parts.append("when=\(when)")
        }
        if let formatCode, !formatCode.isEmpty {
            parts.append("format_code=\(formatCode)")
        }
        let query = parts.joined(separator: "&")
        return try await request("GET", path: "/v1/orgs/\(slug)/fixtures?\(query)")
    }

    func publicFixture(slug: String, id: UUID) async throws -> FixtureDTO {
        try await request("GET", path: "/v1/orgs/\(slug)/fixtures/\(id.uuidString)")
    }
}
