import { Component, AfterViewInit, OnDestroy, Renderer2, Inject, PLATFORM_ID } from '@angular/core';
import { CommonModule } from '@angular/common';
import { isPlatformBrowser } from '@angular/common';

@Component({
  selector: 'app-home',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements AfterViewInit, OnDestroy {
  private scrollListener: any;
  private observer: IntersectionObserver | null = null;

  constructor(
    private renderer: Renderer2,
    @Inject(PLATFORM_ID) private platformId: Object
  ) {}

  ngAfterViewInit() {
    if (isPlatformBrowser(this.platformId)) {
      this.initNavbarScroll();
      this.initStars();
      this.initAboutSectionAnimation();
      this.initSmoothScroll();
      this.initGenieInteractions();
      this.initButtonInteractions();
    }
  }

  ngOnDestroy() {
    if (isPlatformBrowser(this.platformId)) {
      if (this.scrollListener) {
        this.scrollListener();
      }
      if (this.observer) {
        this.observer.disconnect();
      }
    }
  }

  private initNavbarScroll() {
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
  }

  private initStars() {
    this.createInitialStars();
    this.scheduleStarCreation();
  }

  private createInitialStars() {
    for (let i = 0; i < 12; i++) {
      setTimeout(() => this.createStar(), i * 200);
    }
  }

  private scheduleStarCreation() {
    const scheduleNextStar = () => {
      const delay = window.innerWidth <= 768 ? 
        800 + Math.random() * 800 : 
        800 + Math.random() * 700;
      setTimeout(() => {
        this.createStar();
        scheduleNextStar();
      }, delay);
    };
    scheduleNextStar();
  }

  private createStar() {
    const starsContainer = document.getElementById('starsContainer');
    if (!starsContainer) return;

    const star = document.createElement('div');
    star.className = 'star';
    star.innerHTML = '✦';
    
    const genie = document.querySelector('.genie-container');
    if (!genie) return;

    const genieRect = genie.getBoundingClientRect();
    const centerX = genieRect.left + (genieRect.width / 2);
    const centerY = genieRect.top + (genieRect.height / 2);
    
    const angle = Math.random() * Math.PI * 2;
    const radius = window.innerWidth <= 768 ? 
      Math.min(window.innerWidth, window.innerHeight) * 0.25 : 
      Math.min(window.innerWidth, window.innerHeight) * 0.3;
    
    const x = centerX + Math.cos(angle) * radius;
    const y = centerY + Math.sin(angle) * radius;
    
    star.style.left = x + 'px';
    star.style.top = y + 'px';
    
    const sizeRandom = Math.random();
    if (sizeRandom > 0.8) {
      star.classList.add('large');
    } else if (sizeRandom < 0.2) {
      star.classList.add('small');
    }
    
    const duration = 4 + Math.random() * 2;
    star.style.animationDuration = `${duration}s`;
    star.style.animationDelay = `${Math.random() * 2}s`;
    
    starsContainer.appendChild(star);
    
    setTimeout(() => {
      if (star.parentNode) {
        star.parentNode.removeChild(star);
      }
    }, duration * 1000 + 2000);
  }

  private initAboutSectionAnimation() {
    this.observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
        } else {
          entry.target.classList.remove('visible');
        }
      });
    }, {
      threshold: 0.2,
      rootMargin: '0px'
    });

    const aboutSection = document.querySelector('.about-section');
    if (aboutSection) {
      this.observer.observe(aboutSection);
    }
  }

  private initSmoothScroll() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
      anchor.addEventListener('click', (e) => {
        e.preventDefault();
        const href = anchor.getAttribute('href');
        if (href) {
          const target = document.querySelector(href);
          if (target) {
            target.scrollIntoView({
              behavior: 'smooth',
              block: 'start'
            });
          }
        }
      });
    });
  }

  private initGenieInteractions() {
    const genie = document.querySelector('.genie-container');
    if (genie) {
      genie.addEventListener('mouseenter', () => {
        genie.setAttribute('style', 'transform: scale(1.05)');
      });

      genie.addEventListener('mouseleave', () => {
        genie.setAttribute('style', 'transform: scale(1)');
      });
    }
  }

  private initButtonInteractions() {
    const button = document.querySelector('.cta-button');
    const genie = document.querySelector('.genie-container');
    
    if (button) {
      button.addEventListener('click', (e) => {
        e.preventDefault();
        
        // Button animation
        button.setAttribute('style', 'transform: scale(0.95)');
        setTimeout(() => {
          button.setAttribute('style', 'transform: scale(1)');
        }, 150);
        
        // Create extra stars
        for (let i = 0; i < 12; i++) {
          setTimeout(() => this.createStar(), i * 50);
        }

        // Glow effect
        button.setAttribute('style', 'box-shadow: 0 0 30px rgba(56, 175, 130, 0.6)');
        setTimeout(() => {
          button.setAttribute('style', 'box-shadow: none');
        }, 1000);

        // Genie bounce
        if (genie) {
          genie.setAttribute('style', 'transform: translateY(-20px)');
          setTimeout(() => {
            genie.setAttribute('style', 'transform: translateY(0)');
          }, 500);
        }

        // Navigate to login
        setTimeout(() => {
          window.location.href = '/login';
        }, 1000);
      });
    }
  }

  onStarClick(event: MouseEvent) {
    this.createStar();
  }
} 