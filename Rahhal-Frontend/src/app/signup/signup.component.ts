import { Component, AfterViewInit, OnDestroy, Renderer2, Inject, PLATFORM_ID } from '@angular/core';
import { FormBuilder, FormGroup, Validators, ReactiveFormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../services/auth.service';
import { CommonModule } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-signup',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule],
  templateUrl: './signup.component.html',
  styleUrl: './signup.component.css'
})
export class SignupComponent implements AfterViewInit, OnDestroy {
  signupForm: FormGroup;
  loading = false;
  private scrollListener: any;
  private particleSystem: any;

  constructor(
    private fb: FormBuilder,
    private authService: AuthService,
    private router: Router,
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {
    this.signupForm = this.fb.group({
      fullName: ['', [Validators.required, Validators.minLength(2)]],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      confirmPassword: ['', [Validators.required]]
    }, { validators: this.passwordsMatchValidator });
  }

  ngAfterViewInit() {
    if (isPlatformBrowser(this.platformId)) {
      // Navbar scroll effect
      this.scrollListener = this.renderer.listen('window', 'scroll', () => {
        const navbar = document.querySelector('.navbar');
        if (navbar) {
          if (window.scrollY > 50) {
            navbar.classList.add('scrolled');
          } else {
            navbar.classList.remove('scrolled');
          }
        }
      });

      // Initialize particles
      this.initParticles();
    }
  }

  ngOnDestroy() {
    if (isPlatformBrowser(this.platformId)) {
      if (this.scrollListener) {
        this.scrollListener();
      }
      // Remove particle canvas if present
      const canvas = document.getElementById('signup-particles-canvas');
      if (canvas && canvas.parentNode) {
        canvas.parentNode.removeChild(canvas);
      }
    }
  }

  // --- Particle system logic (from particles.js) ---
  initParticles() {
    class Particle {
      x: number;
      y: number;
      size: number;
      speedX: number;
      speedY: number;
      color: string;
      ctx: CanvasRenderingContext2D;
      canvas: HTMLCanvasElement;
      constructor(canvas: HTMLCanvasElement) {
        this.canvas = canvas;
        this.ctx = canvas.getContext('2d')!;
        this.x = Math.random() * canvas.width;
        this.y = Math.random() * canvas.height;
        this.size = 2;
        this.speedX = (Math.random() - 0.5) * 0.1;
        this.speedY = (Math.random() - 0.5) * 0.1;
        this.color = Math.random() > 0.5 ? '#ffffff' : '#38af82';
      }
      update() {
        this.x += this.speedX;
        this.y += this.speedY;
        if (this.x < 0 || this.x > this.canvas.width) this.speedX *= -1;
        if (this.y < 0 || this.y > this.canvas.height) this.speedY *= -1;
      }
      draw() {
        this.ctx.beginPath();
        this.ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        this.ctx.fillStyle = this.color;
        this.ctx.shadowBlur = 20;
        this.ctx.shadowColor = this.color;
        this.ctx.fill();
        this.ctx.shadowBlur = 0;
      }
    }
    class ParticleSystem {
      canvas: HTMLCanvasElement;
      ctx: CanvasRenderingContext2D;
      particles: Particle[] = [];
      numberOfParticles = 30;
      animationFrameId: number | null = null;
      constructor() {
        this.canvas = document.createElement('canvas');
        this.canvas.id = 'signup-particles-canvas';
        this.ctx = this.canvas.getContext('2d')!;
        this.resize();
        window.addEventListener('resize', () => this.resize());
        for (let i = 0; i < this.numberOfParticles; i++) {
          this.particles.push(new Particle(this.canvas));
        }
        this.canvas.style.position = 'fixed';
        this.canvas.style.top = '0';
        this.canvas.style.left = '0';
        this.canvas.style.width = '100%';
        this.canvas.style.height = '100%';
        this.canvas.style.pointerEvents = 'none';
        this.canvas.style.zIndex = '1';
        document.body.appendChild(this.canvas);
        this.animate();
      }
      resize() {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
      }
      animate() {
        this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
        this.particles.forEach(particle => {
          particle.update();
          particle.draw();
        });
        this.animationFrameId = requestAnimationFrame(() => this.animate());
      }
    }
    this.particleSystem = new ParticleSystem();
  }

  passwordsMatchValidator(form: FormGroup) {
    const password = form.get('password')?.value;
    const confirmPassword = form.get('confirmPassword')?.value;
    return password === confirmPassword ? null : { passwordsMismatch: true };
  }

  getErrorMessage(controlName: string): string {
    const control = this.signupForm.get(controlName);
    if (!control) return '';
    if (control.hasError('required')) return 'This field is required';
    if (control.hasError('email')) return 'Invalid email address';
    if (control.hasError('minlength')) {
      const min = control.getError('minlength').requiredLength;
      return `Minimum length is ${min}`;
    }
    if (controlName === 'confirmPassword' && this.signupForm.hasError('passwordsMismatch')) {
      return 'Passwords do not match';
    }
    return '';
  }

  onSubmit() {
    if (this.signupForm.invalid) return;
    this.loading = true;
    const { fullName, email, password } = this.signupForm.value;
    this.authService.register({
      name: fullName,
      email,
      password,
      confirmPassword: this.signupForm.value.confirmPassword
    }).subscribe({
      next: () => {
        this.loading = false;
        this.router.navigate(['/login']);
      },
      error: (err) => {
        this.loading = false;
      }
    });
  }
}
