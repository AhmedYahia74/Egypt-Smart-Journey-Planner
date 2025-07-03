import { Component } from '@angular/core';
import { ChatInputComponent } from '../chat-input/chat-input.component';
import { ChatHeaderComponent } from '../chat-header/chat-header.component';
import { ChatMessagesComponent } from '../chat-messages/chat-messages.component';
import { ChatSidebarComponent } from '../chat-sidebar/chat-sidebar.component';
import { ChatWelcomeComponent } from '../chat-welcome/chat-welcome.component';

@Component({
  selector: 'app-chatbot-page',
  templateUrl: './chatbot-page.component.html',
  imports: [ChatInputComponent,
    ChatHeaderComponent,
    ChatMessagesComponent,
    ChatSidebarComponent,
    ChatWelcomeComponent
  ],
  styleUrls: ['./chatbot-page.component.css']
})
export class ChatbotPageComponent {} 