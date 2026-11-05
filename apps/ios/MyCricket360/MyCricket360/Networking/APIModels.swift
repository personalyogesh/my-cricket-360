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

struct FixtureDTO: Codable, Identifiable {
    let id: UUID
    let schedule_id: UUID?
    let season: String
    let competition: String
    let home_team_id: UUID?
    let away_team_id: UUID?
    let home_team_name: String
    let away_team_name: String
    let venue: String
    let starts_at: String
    let timezone: String
    let format_code: String
    let format_name: String
    let overs: Int?
    let status: String
    let result_summary: String?
}

struct FixturePageDTO: Codable {
    let items: [FixtureDTO]
    let total: Int
    let limit: Int
    let offset: Int
}

struct ScheduleDTO: Codable, Identifiable {
    let id: UUID
    let name: String
    let season: String
    let competition: String
    let format_code: String
    let format_name: String
    let overs: Int?
    let timezone: String
    let status: String
}

struct MembershipRequestDTO: Codable {
    let organization_slug: String
    let role: String
}
