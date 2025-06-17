import { Component, OnInit, OnDestroy } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { log } from 'console';

interface Message {
  text: string;
  sender: 'user' | 'bot';
  timestamp: Date;
  options?: string[];
  buttons?: Array<{
    title: string;
    payload: string;
  }>;
  plan?: {
    plan_combinations: Array<{
      hotel: {
        name: string;
        price_per_night: number;
        location: string;
        rating: number;
        amenities: string[];
      };
      activities: Array<{
        name: string;
        price: number;
        duration: string;
        description: string;
      }>;
      landmarks: Array<{
        name: string;
        price: number;
        description: string;
      }>;
      total_plan_cost: number;
    }>;
  };
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
export class ChatbotComponent implements OnInit, OnDestroy {
  private socket: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectTimeout: any = null;

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

  public messages: Message[] = [];
  public newMessage: string = '';
  public isTyping: boolean = false;
  public connectionStatus: 'connected' | 'disconnected' | 'connecting' = 'disconnected';

  ngOnInit() {
    this.connectWebSocket();
  }

  ngOnDestroy() {
    this.cleanup();
  }

  private cleanup() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
    }
    if (this.socket) {
      this.socket.close();
    }
  }

  private addSystemMessage(text: string) {
    console.log(text);
  }

  private connectWebSocket() {
    if (this.socket?.readyState === WebSocket.OPEN) {
      return;
    }

    this.connectionStatus = 'connecting';
    try {
      this.socket = new WebSocket('ws://localhost:8000/ws/123');

      this.socket.onopen = () => {
        console.log('WebSocket connection established');
        this.connectionStatus = 'connected';
        this.reconnectAttempts = 0;
        this.addSystemMessage('Connected to chat server');
      };

      this.socket.onmessage = (event) => {
        try {
          const messageData = JSON.parse(event.data);
          console.log('Received JSON:', messageData);

          if (messageData.type === 'user_message') {
            // Optional: Ignore echo
            return;
          }

          const message: Message = {
            text: messageData.text || '',
            sender: 'bot',
            timestamp: new Date()
          };

          // Handle buttons
          if (messageData.buttons) {
            message.buttons = messageData.buttons;
            message.options = messageData.buttons.map((button: { title: string }) => button.title);
          }

          // Handle plan
          if (messageData.plan_combinations) {
            message.plan = {
              plan_combinations: messageData.plan_combinations
            };
          }

          this.messages.push(message);
          this.isTyping = false;

        } catch (error) {
          console.error('Error parsing WebSocket JSON message:', error);
        }
      };


      this.socket.onerror = (error) => {
        console.error('WebSocket error:', error);
        this.connectionStatus = 'disconnected';
        this.addSystemMessage('Connection error occurred');
      };

      this.socket.onclose = () => {
        console.log('WebSocket connection closed');
        this.connectionStatus = 'disconnected';
        this.attemptReconnect();
      };

    } catch (error) {
      console.error('Failed to create WebSocket connection:', error);
      this.connectionStatus = 'disconnected';
      this.attemptReconnect();
    }
  }

  private attemptReconnect() {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      this.addSystemMessage(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);

      this.reconnectTimeout = setTimeout(() => {
        this.connectWebSocket();
      }, 5000);
    } else {
      console.log('Max reconnection attempts reached');
      this.addSystemMessage('Failed to connect to chat server. Please refresh the page to try again.');
    }
  }

  public sendMessage(): void {
    if (!this.newMessage.trim() || this.connectionStatus !== 'connected') return;

    const messageToSend = this.newMessage.trim();
    console.log('Sending message:', messageToSend);

    const userMsg: Message = {
      text: messageToSend,
      sender: 'user',
      timestamp: new Date()
    };

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.messages.push(userMsg);  // Add user message to chat
      this.isTyping = true;         // Start typing animation
      this.newMessage = '';         // Clear input
      this.socket.send(messageToSend);  // Send message to server
    } else {
      this.addSystemMessage('Message could not be sent. Connection lost.');
    }
  }

  public selectOption(option: string): void {
    if (this.connectionStatus !== 'connected') return;

    // Find the corresponding button payload
    const lastBotMessage = this.messages[this.messages.length - 1];
    const selectedButton = lastBotMessage.buttons?.find(button => button.title === option);
    const payload = selectedButton?.payload || option;

    const userMsg: Message = {
      text: option,
      sender: 'user',
      timestamp: new Date()
    };

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.messages.push(userMsg);
      this.isTyping = true;
      this.socket.send(payload);
    } else {
      this.addSystemMessage('Option could not be sent. Connection lost.');
    }
  }
}
