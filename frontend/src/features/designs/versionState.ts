import type { DesignVersion } from './types'

function sortedJson<T>(items: T[], key: (item: T) => string) {
  return items.map(key).sort()
}

/** True when the editable draft differs from the latest published snapshot. */
export function hasUnpublishedChanges(draft: DesignVersion | null, published: DesignVersion | null) {
  if (!draft) return false
  if (!published) return true

  const translations = (version: DesignVersion) => sortedJson(
    version.translations,
    item => JSON.stringify([item.locale, item.name, item.description]),
  )
  const selections = (version: DesignVersion) => sortedJson(
    version.selections,
    item => JSON.stringify([item.option_group, item.style_option, item.selected_code, item.selected_name_en]),
  )
  const references = (version: DesignVersion) => sortedJson(
    version.references,
    item => JSON.stringify([
      item.source,
      item.style_option_id ?? '',
      item.style_option_image_id ?? '',
      item.mime_type,
      item.byte_size,
      item.width,
      item.height,
      item.alt_text ?? '',
    ]),
  )

  return JSON.stringify([translations(draft), selections(draft), references(draft)]) !==
    JSON.stringify([translations(published), selections(published), references(published)])
}
