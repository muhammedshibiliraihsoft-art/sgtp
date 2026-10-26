import { ImageOff, RotateCcw } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { usePrivateImage } from '../../hooks/usePrivateImage'

type ImageSource = { content_url: string; alt_text?: string | null }

export function PrivateReferenceImage({ image, alt }: { image?: ImageSource; alt: string }) {
  const { t } = useTranslation()
  const frameRef = useRef<HTMLDivElement>(null)
  const [isNearViewport, setIsNearViewport] = useState(false)
  const { objectUrl, isLoading, error, retry } = usePrivateImage(isNearViewport ? image?.content_url : null)

  useEffect(() => {
    if (!image?.content_url || isNearViewport) return
    const frame = frameRef.current
    if (!frame || typeof IntersectionObserver === 'undefined') {
      setIsNearViewport(true)
      return
    }
    const observer = new IntersectionObserver(([entry]) => {
      if (entry.isIntersecting) {
        setIsNearViewport(true)
        observer.disconnect()
      }
    }, { rootMargin: '180px' })
    observer.observe(frame)
    return () => observer.disconnect()
  }, [image?.content_url, isNearViewport])

  let contents
  if (!image) contents = <div className="measurement-image-fallback" aria-label={t('measurements.noReference')}><ImageOff size={20} /></div>
  else if (!isNearViewport || isLoading) contents = <div className="measurement-image-fallback" aria-label={t('measurements.loadingReference')} aria-busy="true"><span className="measurement-image-skeleton" /></div>
  else if (error || !objectUrl) contents = <div className="measurement-image-fallback measurement-image-error" aria-label={t('measurements.referenceUnavailable')}>
    <ImageOff size={20} />
    <span className="measurement-image-error-text">{t('measurements.referenceUnavailable')}</span>
    <button type="button" className="measurement-image-retry" onClick={event => { event.stopPropagation(); retry() }} aria-label={t('measurements.retryImage', 'Retry image loading')} title={t('measurements.retryImage', 'Retry image loading')}>
      <RotateCcw size={14} />
    </button>
  </div>
  else contents = <img className="measurement-option-image" src={objectUrl} alt={image.alt_text || alt} loading="lazy" />

  return <div ref={frameRef} className="measurement-image-frame">{contents}</div>
}

export function PrivateReferenceGallery({ images, alt }: { images: ImageSource[]; alt: string }) {
  if (!images.length) return <PrivateReferenceImage alt={alt} />
  return <div className="measurement-reference-gallery" aria-label={alt}>
    {images.map((image, index) => <PrivateReferenceImage key={image.content_url} image={image} alt={`${alt} ${index + 1}`} />)}
  </div>
}
