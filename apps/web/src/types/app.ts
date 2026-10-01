export type AuthMode = 'login' | 'signup'
export type ProfileVisibility = 'public' | 'discoverable' | 'limited' | 'hidden'
export type TravelIntent =
  | 'dating_romantic'
  | 'serious_relationship'
  | 'casual_dating'
  | 'travel_companion'
  | 'friends_social'
  | 'local_guide'
  | 'activity_partner'

export type OnboardingDraft = {
  ageConfirmed: boolean
  displayName: string
  dateOfBirth: string
  bio: string
  genderIdentity: string
  datingPreference: string
  discoveryPreference: string
  travelIntentions: TravelIntent[]
  languages: string[]
  interests: string[]
  profileVisibility: ProfileVisibility
  locationPrivacy: 'hidden' | 'approximate' | 'destination'
  exactLocationSharing: boolean
}
