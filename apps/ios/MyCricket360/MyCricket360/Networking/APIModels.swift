import Foundation

struct APIErrorBody: Decodable {
    let detail: String?
}

struct ProfileDTO: Codable, Identifiable {
    let id: UUID
    let email: String?
    let display_name: String
    let avatar_url: String?
    let phone: String?
}

struct MembershipDTO: Codable, Identifiable {
    let id: UUID
    let organization_id: UUID
    let organization_slug: String
    let organization_name: String
    let user_id: UUID?
    let email: String?
    let display_name: String?
    let role: String
    let status: String
    let requested_at: String
    let decided_at: String?
}

struct MeDTO: Codable {
    let user: ProfileDTO
    let memberships: [MembershipDTO]
    let approved_clubs: [MembershipDTO]
}

struct TeamDTO: Codable, Identifiable {
    let id: UUID
    let name: String
    let division: String?
    let season: String?
}

struct SponsorDTO: Codable, Identifiable {
    let id: UUID
    let slug: String
    let name: String
    let tagline: String?
    let description: String?
    let website_url: String?
    let logo_url: String?
    let banner_url: String?
    let status: String
    let sort_order: Int
}

struct DevTokenResponseDTO: Codable {
    let access_token: String
    let token_type: String
    let user: ProfileDTO
    let note: String
}

struct MembershipRequestDTO: Codable {
    let organization_slug: String
    let role: String
}
