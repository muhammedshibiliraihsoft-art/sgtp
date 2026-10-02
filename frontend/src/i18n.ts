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
              more: '+ {{count}} more' },
      backoffice: {
        eyebrow: 'Main Supplier', navigation: 'Back Office navigation', mainSupplier: 'Main Supplier',
        dashboard: 'Dashboard', dashboardIntro: 'Manage your Shops from one clear place.',
        manageShops: 'Your Shops', manageIntro: 'View Shop details, create a Shop, and manage its status.',
        viewShops: 'View Shops', shops: 'Shops', shop: 'Shop', createShop: 'Create Shop',
        shopCount_one: '{{count}} Shop', shopCount_other: '{{count}} Shops',
        searchShops: 'Find a Shop', searchPlaceholder: 'Search by name or slug',
        filterStatus: 'Status', allShops: 'All Shops', sortBy: 'Sort by', nameAscending: 'Name A–Z',
        nameDescending: 'Name Z–A', newest: 'Newest', oldest: 'Oldest',
        status: 'Status', active: 'Active', inactive: 'Inactive', users: 'users',
        locale: 'Language', currency: 'Currency', timezone: 'Time zone', open: 'Open',
        loading: 'Loading Shops…', loadFailed: 'Unable to load Shops.', noShops: 'No Shops found',
        noShopsHint: 'Create a Shop to get started, or try another search.',
        previous: 'Previous', next: 'Next', page: 'Page {{page}}', signOut: 'Sign out',
        backToShops: 'Back to Shops', createIntro: 'Set up the Shop and its first Admin account together.',
        shopDetails: 'Shop details', shopDetailsHint: 'Give this Shop a clear name and capacity.',
        shopName: 'Shop name', slug: 'Slug', slugHint: 'Lowercase letters, numbers, and hyphens.',
        maxUsers: 'Maximum users', firstAdmin: 'First Shop Admin',
        firstAdminHint: 'This person receives a generated User ID and temporary password.',
        firstName: 'First name', lastName: 'Last name', email: 'Email', phone: 'Phone',
        phoneCountryCode: 'Country code',
        phoneHint: 'Choose Kuwait (+965) or India (+91), then enter the phone number.',
        optionalSettings: 'Optional Shop settings', optionalHint: 'You can update these later.',
        contactEmail: 'Contact email', contactPhone: 'Contact phone', useDefault: 'Use default',
        address: 'Address', addressLine1: 'Address line 1', addressLine2: 'Address line 2',
        city: 'City', state: 'State / region', postalCode: 'Postal code', country: 'Country',
        currencyHint: 'Three-letter code, for example INR.', timezoneHint: 'For example Asia/Kolkata.',
        cancel: 'Cancel', saving: 'Saving…', saveFailed: 'Unable to save the Shop.',
        createdTitle: 'Shop created successfully', createdMessage: '{{name}} is ready. Save the first Admin credentials now.',
        userId: 'First Admin User ID', temporaryPassword: 'Temporary password',
        copy: 'Copy', show: 'Show', hide: 'Hide', copyBoth: 'Copy both', both: 'both credentials',
        copied: '{{item}} copied.', copyFailed: 'Unable to copy. Please select the credential manually.',
        saveCredentialsNow: 'Save these credentials now. The temporary password is shown only in this creation response.',
        doneOpenShop: 'Done · Open Shop', editShop: 'Edit Shop', saveChanges: 'Save changes',
        activate: 'Activate Shop', deactivate: 'Deactivate Shop',
        confirmActivate: 'Activate {{name}}?', confirmDeactivate: 'Deactivate {{name}}?',
        createdAt: 'Created',
      },
      clients: {
        title: 'Clients',
        subtitle: 'Manage your shop clients and related persons.',
        addClient: 'Add Client',
        addRelatedPerson: 'Add Related Person',
        searchPlaceholder: 'Search by name, phone or Client ID',
        noClients: 'No clients yet',
        noClientsHint: 'Add your first client to start building your client list.',
        noRelated: 'No related persons added',
        relatedPersons: 'Related Persons',
        edit: 'Edit',
        remove: 'Remove',
        save: 'Save Changes',
        cancel: 'Cancel',
        possibleDuplicate: 'Possible duplicate',
        duplicateHint: 'Another client may already use this phone number.',
        matchedClients: 'Matched clients:',
        name: 'Name',
        phone: 'Phone',
        email: 'Email',
        created: 'Created',
        lastUpdated: 'Last Updated',
        actions: 'Actions',
        confirmRemove: 'Remove this client from the active client list?',
        confirmRemoveRelated: 'Remove this related person from the active list?'
      }
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
