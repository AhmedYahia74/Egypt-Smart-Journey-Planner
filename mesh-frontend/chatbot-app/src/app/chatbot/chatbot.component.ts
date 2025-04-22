import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
}

interface User {
  id: number;
  name: string;
  avatarUrl: string;
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
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
      text: 'Hello, this is a custom chat demo.',
      sender: 'bot',
      timestamp: new Date()
    },
    {
      text: 'Looks amazing!',
      sender: 'user',
      timestamp: new Date()
    }
  ];

  public newMessage: string = '';
  public isTyping: boolean = false;

  public sendMessage(): void {
    if (!this.newMessage.trim()) return;

    const userMsg: Message = {
      text: this.newMessage,
      sender: 'user',
      timestamp: new Date()
    };

    this.messages.push(userMsg);
    this.newMessage = '';
    this.isTyping = true;

    setTimeout(() => {
      const botReply: Message = {
        text: this.getBotReply(userMsg.text),
        sender: 'bot',
        timestamp: new Date()
      };
      this.isTyping = false;
      this.messages.push(botReply);
    }, 2000);
  }

  private getBotReply(input: string): string {
    if (input.toLowerCase().includes('hello')) {
      return 'Hi there! How can I help you today?';
    }
    return "I'm here to assist you!";
  }
}
