import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { KENDO_BUTTONS } from "@progress/kendo-angular-buttons";
import {
  KENDO_INPUTS,
  TextAreaComponent,
} from "@progress/kendo-angular-inputs";
import { SVGIcon, imageIcon, xCircleIcon } from "@progress/kendo-svg-icons";

import {
  ChatModule,
  Message,
  SendMessageEvent,
  User
} from '@progress/kendo-angular-conversational-ui';

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule, ChatModule, KENDO_BUTTONS, KENDO_INPUTS, TextAreaComponent],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.css']
})
export class ChatbotComponent {
  public bot: User = {
    id: 0,
    name: 'Rahhal',
    avatarUrl: 'https://img.freepik.com/premium-vector/chat-bot-logo-virtual-assistant-bot-icon-logo-robot-head-with-headphones_843540-99.jpg',
  };

  public user: User = {
    id: 1,
    name: 'John',
    avatarUrl: 'https://www.shutterstock.com/image-vector/default-avatar-profile-icon-social-600nw-1677509740.jpg',
  };

  public messages: Message[] = [
    {
      author: this.bot,
      text: 'Hello, this is a Kendo Chat demo.'
    },
    {
      author: this.user,
      text: 'Looks amazing!'
    }
  ];

  
  public sendMessage(event: SendMessageEvent): void {
    const userMsg = event.message;
    this.messages = [...this.messages, userMsg];

    setTimeout(() => {
      this.messages = [...this.messages, {
        author: this.bot,
        text: this.getBotReply(userMsg.text || '')
      }];
    }, 500);
  }

  private getBotReply(input: string): string {
    if (input.toLowerCase().includes('hello')) {
      return 'Hi there! How can I help you today?';
    }
    return "I'm here to assist you!";
  }
}
