import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'

const resources = {
  en: {
    translation: {
      welcomeBack: 'Welcome back', goodMorning: 'Good morning, Alex',
      nav: { dashboard: 'Dashboard', work: 'Work', orders: 'Orders', clients: 'Clients', billing: 'Billing', more: 'More' },
      more: { reports: 'Reports', members: 'Members', workFunctions: 'Work Functions', settings: 'Settings', shopProfile: 'Shop Profile', preferences: 'Preferences', help: 'Help & Support' },
      work: { title: 'Work', subtitle: 'Every order. Every step. One clear view.', newOrder: 'New Order',
              metrics: { newOrders: 'New Orders', inProgress: 'In Progress', ready: 'Ready', overdue: 'Overdue' },
              stages: { cutting: 'Cutting', stitching: 'Stitching', finishing: 'Finishing', ready: 'Ready' },
              more: '+ {{count}} more' }
    }
  },
  'ar-KW': {
    translation: {
      welcomeBack: 'مرحبًا بعودتك', goodMorning: 'صباح الخير، أليكس',
      nav: { dashboard: 'لوحة القيادة', work: 'العمل', orders: 'الطلبات', clients: 'العملاء', billing: 'الفواتير', more: 'المزيد' },
      more: { reports: 'التقارير', members: 'الأعضاء', workFunctions: 'وظائف العمل', settings: 'الإعدادات', shopProfile: 'ملف المتجر', preferences: 'التفضيلات', help: 'المساعدة والدعم' },
      work: { title: 'العمل', subtitle: 'كل طلب. كل خطوة. رؤية واضحة واحدة.', newOrder: 'طلب جديد',
              metrics: { newOrders: 'طلبات جديدة', inProgress: 'قيد التقدم', ready: 'جاهز', overdue: 'متأخر' },
              stages: { cutting: 'القص', stitching: 'الخياطة', finishing: 'التشطيب', ready: 'جاهز' },
              more: '+ {{count}} المزيد' }
    }
  },
  bn: {
    translation: {
      welcomeBack: 'আবার স্বাগতম', goodMorning: 'সুপ্রভাত, অ্যালেক্স',
      nav: { dashboard: 'ড্যাশবোর্ড', work: 'কাজ', orders: 'অর্ডার', clients: 'ক্লায়েন্ট', billing: 'বোলিং', more: 'আরও' },
      more: { reports: 'রিপোর্ট', members: 'সদস্যরা', workFunctions: 'কাজের ফাংশন', settings: 'সেটিংস', shopProfile: 'দোকান প্রোফাইল', preferences: 'পছন্দসমূহ', help: 'সাহায্য ও সমর্থন' },
      work: { title: 'কাজ', subtitle: 'প্রতিটি অর্ডার. প্রতিটি ধাপ. এক পরিষ্কার দৃশ্য.', newOrder: 'নতুন অর্ডার',
              metrics: { newOrders: 'নতুন অর্ডার', inProgress: 'চলমান', ready: 'প্রস্তুত', overdue: 'বিলম্বে' },
              stages: { cutting: 'কাটিং', stitching: 'সেলাই', finishing: 'ফিনিশিং', ready: 'প্রস্তুত' },
              more: '+ {{count}} আরও' }
    }
  },
  ur: {
    translation: {
      welcomeBack: 'خوش آمدید', goodMorning: 'صبح بخیر، الیکس',
      nav: { dashboard: 'ڈیش بورڈ', work: 'کام', orders: 'احکامات', clients: 'کلائنٹس', billing: 'بلنگ', more: 'مزید' },
      more: { reports: 'رپورٹس', members: 'اراکین', workFunctions: 'کام کے افعال', settings: 'ترتیبات', shopProfile: 'دکان پروفائل', preferences: 'ترجیحات', help: 'مدد اور تعاون' },
      work: { title: 'کام', subtitle: 'ہر آرڈر۔ ہر قدم۔ ایک واضح منظر۔', newOrder: 'نیا آرڈر',
              metrics: { newOrders: 'نئے احکامات', inProgress: 'جاری ہے', ready: 'تیار', overdue: 'تاخیر' },
              stages: { cutting: 'کٹنگ', stitching: 'سلائی', finishing: 'فنشنگ', ready: 'تیار' },
              more: '+ {{count}} مزید' }
    }
  },
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
