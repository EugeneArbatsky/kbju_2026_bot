from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
import database
import texts
from handlers.messages import create_edit_delete_buttons, create_cancel_button, delete_dayresult_messages

async def handle_callback(update: Update, context: CallbackContext):
    """Обработчик callback кнопок"""
    print("🔘 handle_callback вызван!")
    
    query = update.callback_query
    
    if not query:
        print("❌ Callback query is None")
        return
    
    print(f"🔘 Callback query получен: {query.data}")
    
    await query.answer()
    
    user = update.effective_user
    data = query.data
    
    print(f"🔘 Получен callback: {data} от пользователя {user.id}")
    
    try:
        if data.startswith("edit_"):
            # Обработка кнопки "Редактировать"
            # Формат: edit_1,2,3_dayid
            parts = data.split("_")
            print(f"📝 Парсинг callback: parts = {parts}")
            
            if len(parts) >= 3:
                entry_ids_str = parts[1]  # "1,2,3"
                day_id = int(parts[2])
                
                print(f"📝 entry_ids_str = {entry_ids_str}, day_id = {day_id}")
                
                # Парсим список entry_ids
                entry_ids = [int(x) for x in entry_ids_str.split(',')]
                print(f"📝 entry_ids = {entry_ids}")
                
                # Проверяем, что все записи существуют
                for entry_id in entry_ids:
                    entry = database.get_food_entry_by_id(entry_id, user.id)
                    if not entry:
                        print(f"⚠️  Запись {entry_id} не найдена для пользователя {user.id}")
                        await query.message.reply_text(texts.EDIT_NOT_FOUND_TEXT)
                        return
                
                # Сохраняем информацию о редактировании в user_data
                context.user_data['editing_entry_ids'] = entry_ids
                context.user_data['editing_message_id'] = query.message.message_id
                context.user_data['editing_day_id'] = day_id
                
                print(f"✅ Сессия редактирования начата: entry_ids={entry_ids}, message_id={query.message.message_id}")
                
                # Отправляем сообщение с инструкцией и кнопкой "Отменить"
                cancel_markup = create_cancel_button()
                prompt_message = await query.message.reply_text(texts.EDIT_PROMPT_TEXT, reply_markup=cancel_markup)
                # Сохраняем message_id сообщения с инструкцией для последующего удаления
                context.user_data['editing_prompt_message_id'] = prompt_message.message_id
            else:
                print(f"❌ Неверный формат callback_data: {data}, parts = {parts}")
        
        elif data.startswith("delete_"):
            # Обработка кнопки "Удалить"
            # Формат: delete_1,2,3_dayid
            parts = data.split("_")
            print(f"🗑️  Парсинг callback удаления: parts = {parts}")
            
            if len(parts) >= 3:
                entry_ids_str = parts[1]  # "1,2,3"
                day_id = int(parts[2])
                
                print(f"🗑️  entry_ids_str = {entry_ids_str}, day_id = {day_id}")
                
                # Парсим список entry_ids
                entry_ids = [int(x) for x in entry_ids_str.split(',')]
                print(f"🗑️  entry_ids = {entry_ids}")
                
                # Проверяем, что все записи существуют и принадлежат пользователю
                for entry_id in entry_ids:
                    entry = database.get_food_entry_by_id(entry_id, user.id)
                    if not entry:
                        print(f"⚠️  Запись {entry_id} не найдена для пользователя {user.id}")
                        await query.message.reply_text(texts.DELETE_NOT_FOUND_TEXT)
                        return
                
                # Сохраняем chat_id перед удалением сообщения
                chat_id = query.message.chat.id
                
                # Удаляем записи из базы данных
                success = database.delete_food_entries(entry_ids, user.id)
                
                if not success:
                    print(f"❌ Не удалось удалить записи {entry_ids}")
                    await query.message.reply_text(texts.DELETE_ERROR_TEXT)
                    return
                
                # Удаляем сообщение с отчетом о приеме пищи
                try:
                    await context.bot.delete_message(
                        chat_id=chat_id,
                        message_id=query.message.message_id
                    )
                except Exception as e:
                    print(f"⚠️  Не удалось удалить сообщение с отчетом: {e}")
                
                # Удаляем сообщения /dayresult (так как они становятся неактуальными)
                await delete_dayresult_messages(update, context, user.id)
                
                # Отправляем сообщение об успешном удалении
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=texts.DELETE_SUCCESS_TEXT
                )
                
                print(f"✅ Успешно удалены записи {entry_ids} для пользователя {user.id}")
            else:
                print(f"❌ Неверный формат callback_data для удаления: {data}, parts = {parts}")
                await query.message.reply_text(texts.DELETE_ERROR_TEXT)
        
        elif data == "cancel_edit":
            # Отмена редактирования
            # Удаляем сообщение с инструкцией
            prompt_message_id = context.user_data.get('editing_prompt_message_id')
            if prompt_message_id:
                try:
                    await context.bot.delete_message(
                        chat_id=query.message.chat.id,
                        message_id=prompt_message_id
                    )
                except Exception as e:
                    print(f"⚠️  Не удалось удалить сообщение с инструкцией: {e}")
            
            context.user_data.pop('editing_entry_ids', None)
            context.user_data.pop('editing_message_id', None)
            context.user_data.pop('editing_day_id', None)
            context.user_data.pop('editing_prompt_message_id', None)
            await query.message.reply_text(texts.EDIT_CANCEL_TEXT)
        else:
            print(f"⚠️  Неизвестный callback_data: {data}")
    
    except Exception as e:
        print(f"❌ Ошибка при обработке callback: {e}")
        import traceback
        traceback.print_exc()
        try:
            await query.message.reply_text(f"Произошла ошибка: {str(e)}")
        except:
            pass
