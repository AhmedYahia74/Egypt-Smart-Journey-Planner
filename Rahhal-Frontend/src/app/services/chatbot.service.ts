import { Injectable, Inject, PLATFORM_ID } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject, Subject, EMPTY } from 'rxjs';
import { environment } from '../../environments/environment';
import SockJS from 'sockjs-client';
import * as Stomp from '@stomp/stompjs';
import { User } from './auth.service';
import { isPlatformBrowser } from '@angular/common';

@Injectable({ providedIn: 'root' })
export class ChatbotService {
  private apiUrl = environment.apiUrl;
  private wsUrl = 'http://localhost:8088/ws/chatbot';

  private authToken: string | null = null;
  private userId: string | null = null;
  private user: User | null =null;
  private stompClient: any = null;
  private isWebSocketConnected = false;
  private currentConversationId: number | null = null;

  public chatHistory$ = new BehaviorSubject<any[]>([]);
  public messages$ = new Subject<any>();
  public connectionStatus$ = new BehaviorSubject<boolean>(false);

  constructor(
    private http: HttpClient,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    if (isPlatformBrowser(this.platformId)) {
      this.authToken = localStorage.getItem('authToken');
      const userStr = localStorage.getItem('current_user');
      this.user = userStr ? JSON.parse(userStr) as User : null;
      this.userId = this.user?.id ? String(this.user.id) : null;
    }
  }

  fetchChatHistory(): Observable<any> {
    if (!this.userId || !this.authToken) {
      return EMPTY;
    }
    return this.http.get(`${this.apiUrl}/tourist/chats/${this.userId}`, {
      headers: this.getAuthHeaders()
    });
  }

  connectWebSocket(conversationId: number) {
    if (!this.authToken || !this.userId) return;
    this.currentConversationId = conversationId;
    const socket = new SockJS(`${this.wsUrl}?token=${this.authToken}`);
    // @stomp/stompjs does not have a static 'over' method, use Client constructor instead
    this.stompClient = new Stomp.Client({
      webSocketFactory: () => socket,
      debug: () => {}, // disable debug output
      reconnectDelay: 0 // we'll handle reconnection manually
    });
    this.stompClient.onConnect = (frame: any) => {
      this.isWebSocketConnected = true;
      this.connectionStatus$.next(true);
      this.subscribeToConversation(conversationId);
    }, (error: any) => {
      this.isWebSocketConnected = false;
      this.connectionStatus$.next(false);
      // Try to reconnect after 5 seconds
      setTimeout(() => this.connectWebSocket(conversationId), 5000);
      }
    // Unsubscribe from previous if needed
    if (this.stompClient.subscriptions) {
      Object.keys(this.stompClient.subscriptions).forEach(key => {
        this.stompClient.unsubscribe(key);
      });
    }
    this.stompClient.subscribe(`/user/${this.userId}/queue/conversation/${conversationId}`, (message: any) => {
      if (message && message.body) {
        try {
          this.messages$.next(JSON.parse(message.body));
        } catch {
          this.messages$.next(message.body);
        }
      }
    });
  }

  sendMessage(conversationId: number, message: string) {
    if (!this.stompClient || !this.stompClient.connected) return;
    if (!this.userId) return;
    this.stompClient.send(`/app/chatbot/send/${this.userId}/${conversationId}`, {}, message);
  }

  disconnectWebSocket() {
    if (this.stompClient && this.stompClient.connected) {
      this.stompClient.disconnect();
      this.isWebSocketConnected = false;
      this.connectionStatus$.next(false);
    }
  }

  getAuthHeaders(): HttpHeaders {
    return new HttpHeaders({
      'Authorization': `Bearer ${this.authToken}`,
      'Content-Type': 'application/json'
    });
  }

  private subscribeToConversation(conversationId: number) {
    if (!this.stompClient || !this.stompClient.connected) return;
    // Unsubscribe from previous if needed
    if (this.stompClient.subscriptions) {
      Object.keys(this.stompClient.subscriptions).forEach(key => {
        this.stompClient.unsubscribe(key);
      });
    }
    this.stompClient.subscribe(`/user/${this.userId}/queue/conversation/${conversationId}`, (message: any) => {
      if (message && message.body) {
        try {
          this.messages$.next(JSON.parse(message.body));
        } catch {
          this.messages$.next(message.body);
        }
      }
    });
  }
} 