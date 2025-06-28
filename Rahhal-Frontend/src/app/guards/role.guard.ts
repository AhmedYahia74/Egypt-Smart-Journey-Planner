import { Injectable } from '@angular/core';
import { CanActivate, ActivatedRouteSnapshot, RouterStateSnapshot, Router, UrlTree } from '@angular/router';
import { Observable } from 'rxjs';
import { AuthService } from '../services/auth.service';

@Injectable({
  providedIn: 'root'
})
export class RoleGuard implements CanActivate {
  constructor(
    private authService: AuthService,
    private router: Router
  ) {}

  canActivate(
    route: ActivatedRouteSnapshot,
    state: RouterStateSnapshot
  ): Observable<boolean | UrlTree> | Promise<boolean | UrlTree> | boolean | UrlTree {
    const currentUser = this.authService.currentUserValue;
    
    if (!currentUser) {
      // Not authenticated, redirect to login
      return this.router.createUrlTree(['/auth/login']);
    }

    // Check if route has required roles
    const requiredRoles = route.data['roles'] as string[];
    
    if (!requiredRoles || requiredRoles.length === 0) {
      return true; // No roles required
    }

    // Check if user has any of the required roles
    const hasRequiredRole = requiredRoles.includes(currentUser.role);
    
    if (hasRequiredRole) {
      return true;
    }

    // User doesn't have required role, redirect to unauthorized page or dashboard
    return this.router.createUrlTree(['/unauthorized']);
  }
} 