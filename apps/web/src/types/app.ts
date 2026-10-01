export type AuthMode = 'login' | 'signup'
export type ProfileVisibility = 'public' | 'friends' | 'private'
export type TravelIntent =
  | 'dating'
  | 'relationship'
  | 'casual'
  | 'travel-companion'
  | 'friends'
  | 'local-guide'
  | 'activity-partner'

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
  locationPrivacy: string
  exactLocationSharing: boolean
}
