import { Routes } from '@angular/router';
import { ChatbotComponent } from './chatbot/chatbot.component';

export const routes: Routes = [ 
    {
        path: 'home' ,
        component: ChatbotComponent
    },
    {
        path: '**',
        redirectTo: '/home'
    }
];
