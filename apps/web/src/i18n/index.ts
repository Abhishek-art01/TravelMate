import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const english = {
  auth: {
    loginTitle: 'Your next story starts here.',
    signupTitle: 'Make room for a new story.',
    forgotTitle: 'Let’s get you back in.',
    loginAction: 'Sign in',
    signupAction: 'Create account',
    email: 'Email address',
    password: 'Password',
  },
  navigation: {
    home: 'Home',
    profile: 'Profile',
    privacy: 'Privacy',
    signOut: 'Sign out',
  },
}

export const supportedLocales = [
  'en', 'hi', 'bn', 'te', 'mr', 'ta', 'gu', 'kn', 'ml', 'pa', 'or', 'as', 'ur',
] as const

void i18n.use(initReactI18next).init({
  resources: { en: { translation: english } },
  lng: 'en',
  fallbackLng: 'en',
  supportedLngs: [...supportedLocales],
  nonExplicitSupportedLngs: true,
  interpolation: { escapeValue: false },
  returnNull: false,
})

export default i18n
