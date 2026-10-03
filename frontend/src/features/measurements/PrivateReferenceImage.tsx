import { ImageOff } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { usePrivateImage } from '../../hooks/usePrivateImage'

type ImageSource = { content_url: string; alt_text?: string | null }

export function PrivateReferenceImage({ image, alt }: { image?: ImageSource; alt: string }) {
  const { t } = useTranslation()
  const { objectUrl, isLoading, error } = usePrivateImage(image?.content_url)

  if (!image) return <div className="measurement-image-fallback" aria-label={t('measurements.noReference')}><ImageOff size={20} /></div>
  if (isLoading) return <div className="measurement-image-fallback" aria-label={t('measurements.loadingReference')} aria-busy="true"><span className="measurement-image-skeleton" /></div>
  if (error || !objectUrl) return <div className="measurement-image-fallback" aria-label={t('measurements.referenceUnavailable')}><ImageOff size={20} /></div>

  return <img className="measurement-option-image" src={objectUrl} alt={image.alt_text || alt} loading="lazy" />
}

export function PrivateReferenceGallery({ images, alt }: { images: ImageSource[]; alt: string }) {
  if (!images.length) return <PrivateReferenceImage alt={alt} />
  return <div className="measurement-reference-gallery" aria-label={alt}>
    {images.map((image, index) => <PrivateReferenceImage key={image.content_url} image={image} alt={`${alt} ${index + 1}`} />)}
  </div>
}
