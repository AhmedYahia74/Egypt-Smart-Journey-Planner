import { NgModule } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ChatbotPageComponent } from './chatbot-page/chatbot-page.component';
import { ChatHeaderComponent } from './chat-header/chat-header.component';
import { ChatSidebarComponent } from './chat-sidebar/chat-sidebar.component';
import { ChatMessagesComponent } from './chat-messages/chat-messages.component';
import { ChatInputComponent } from './chat-input/chat-input.component';
import { ChatWelcomeComponent } from './chat-welcome/chat-welcome.component';

@NgModule({
  imports: [
    CommonModule,
    FormsModule,
    ChatbotPageComponent,
    ChatHeaderComponent,
    ChatSidebarComponent,
    ChatMessagesComponent,
    ChatInputComponent,
    ChatWelcomeComponent
  ],
  exports: [ChatbotPageComponent]
})
export class ChatbotModule {} 