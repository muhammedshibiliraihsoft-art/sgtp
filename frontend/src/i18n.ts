import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  en: { translation: { welcomeBack: 'Welcome back', goodMorning: 'Good morning, Alex' } },
  'ar-KW': { translation: { welcomeBack: 'مرحبًا بعودتك', goodMorning: 'صباح الخير، أليكس' } },
  bn: { translation: { welcomeBack: 'আবার স্বাগতম', goodMorning: 'সুপ্রভাত, অ্যালেক্স' } },
  ur: { translation: { welcomeBack: 'خوش آمدید', goodMorning: 'صبح بخیر، الیکس' } },
}

void i18n.use(initReactI18next).init({
  resources,
  lng: localStorage.getItem('sgtp-locale') || 'en',
  fallbackLng: 'en',
  supportedLngs: ['en', 'ar-KW', 'bn', 'ur'],
  interpolation: { escapeValue: false },
})

i18n.on('languageChanged', (language) => localStorage.setItem('sgtp-locale', language))

export default i18n
