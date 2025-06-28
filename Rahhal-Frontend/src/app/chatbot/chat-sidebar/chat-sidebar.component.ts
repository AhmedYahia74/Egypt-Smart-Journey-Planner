import { CommonModule } from '@angular/common';
import { Component, OnInit } from '@angular/core';
import { ChatbotService } from '../../services/chatbot.service';
import SockJS from 'sockjs-client';

@Component({
  selector: 'app-chat-sidebar',
  templateUrl: './chat-sidebar.component.html',
  imports: [CommonModule],
  styleUrls: ['./chat-sidebar.component.css']
})
export class ChatSidebarComponent implements OnInit {
  chatHistory: any[] = [];

  constructor(private chatbotService: ChatbotService) {}

  ngOnInit() {
    this.chatbotService.fetchChatHistory().subscribe(history => {
      this.chatHistory = history;
    });
  }
} 