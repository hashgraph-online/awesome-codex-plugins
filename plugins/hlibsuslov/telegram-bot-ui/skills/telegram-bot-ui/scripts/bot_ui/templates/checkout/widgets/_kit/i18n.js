/* Widget kit strings: request outcomes. Uppercase keys are WidgetRequestError codes, lowercase
   keys are the "err" codes the gallery handlers answer with. The build keeps only the language
   blocks asked for (--lang); a widget adds its own strings in blocks of the same form. */
/*@lang en*/K.add({ en: {
  wait: "Sending…", NOT_ALLOWED: "Open the bot for this", BUSY: "One moment…",
  RATE_LIMITED: "Too fast, wait a bit", TIMEOUT: "No answer. Nothing changed",
  FAILED: "Couldn't reach the bot", INVALID_ANSWER: "Unexpected answer",
  stale: "Changed meanwhile, check again", not_allowed: "Only the owner can do this",
  failed: "Not saved, try again", busy: "Busy, try again", bad_request: "Not available"
} });/*@end*/
/*@lang ru*/K.add({ ru: {
  wait: "Отправляю…", NOT_ALLOWED: "Откройте бота", BUSY: "Секунду…",
  RATE_LIMITED: "Слишком часто, подождите", TIMEOUT: "Нет ответа. Ничего не изменилось",
  FAILED: "Бот недоступен", INVALID_ANSWER: "Странный ответ",
  stale: "Уже изменилось, проверьте", not_allowed: "Только для владельца",
  failed: "Не сохранилось", busy: "Занято, повторите", bad_request: "Недоступно"
} });/*@end*/
/*@lang uk*/K.add({ uk: {
  wait: "Надсилаю…", NOT_ALLOWED: "Відкрийте бота", BUSY: "Хвилинку…",
  RATE_LIMITED: "Занадто часто, зачекайте", TIMEOUT: "Немає відповіді. Нічого не змінилося",
  FAILED: "Бот недоступний", INVALID_ANSWER: "Дивна відповідь",
  stale: "Вже змінилося, перевірте", not_allowed: "Лише для власника",
  failed: "Не збереглося", busy: "Зайнято, повторіть", bad_request: "Недоступно"
} });/*@end*/
