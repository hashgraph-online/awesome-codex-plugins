import { defaultLocale } from '@/generated/locale'
import { en } from './en'
import { zh } from './zh'

export const messages = { en, zh } as const
export type LocaleKey = keyof typeof messages
export const locale = messages[defaultLocale] ?? zh

