import React from 'react';
import { ArrowRight, Shield, Zap, BarChart3, Users, FileText, Github, BookOpen, Brain } from 'lucide-react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  const features = [
    {
      title: "AI-Powered Analysis",
      description: "Automatically detect ambiguities, contradictions, and inconsistencies in your requirements",
      icon: <Zap className="h-6 w-6" />
    },
    {
      title: "Visual Traceability",
      description: "Link requirements to generated diagrams and track changes throughout the lifecycle",
      icon: <BarChart3 className="h-6 w-6" />
    },
    {
      title: "Role-Based Access",
      description: "Different interfaces for analysts and supervisors with appropriate permissions",
      icon: <Users className="h-6 w-6" />
    },
    {
      title: "Document Validation",
      description: "Ensure your SRS documents meet industry standards and best practices",
      icon: <FileText className="h-6 w-6" />
    }
  ];

  const testimonials = [
    {
      quote: "VisSpec transformed how we handle requirements validation. The AI analysis caught issues we missed for months.",
      author: "Sarah Johnson",
      role: "Lead Developer, TechCorp"
    },
    {
      quote: "The traceability features helped us maintain alignment between requirements and implementation throughout the project.",
      author: "Michael Chen",
      role: "Product Manager, InnovateCo"
    }
  ];

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      {/* Navigation */}
      <nav className="bg-[var(--card-bg)] border-b border-[var(--card-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <div className="flex-shrink-0 flex items-center">
                <Brain className="h-8 w-8 text-[var(--primary-main)]" />
                <span className="ml-2 text-xl font-bold text-[var(--text-primary)]">VisSpec</span>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <Link
                to="/login"
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3 py-2 rounded-md text-sm font-medium"
              >
                Sign In
              </Link>
              <Link
                to="/login"
                className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[var(--primary-hover)] hover:text-white transition-colors"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <div className="relative overflow-hidden bg-gradient-to-br from-[var(--content-bg)] to-[var(--surface-bg)]">
        <div className="max-w-7xl mx-auto py-24 px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="flex justify-center">
              <div className="p-4 bg-[var(--primary-main)]/10 rounded-full">
                <Brain className="h-12 w-12 text-[var(--primary-main)]" />
              </div>
            </div>
            <h1 className="mt-6 text-4xl tracking-tight font-extrabold text-[var(--text-primary)] sm:text-5xl md:text-6xl">
              <span className="block">AI-Powered Requirements</span>
              <span className="block text-[var(--primary-main)] mt-2">Validation & Visualization</span>
            </h1>
            <p className="mt-6 max-w-lg mx-auto text-lg text-[var(--text-secondary)] sm:max-w-3xl">
              Transform your SRS documents into validated, visual specifications with AI-driven analysis and comprehensive traceability.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-medium rounded-lg text-white bg-[var(--primary-main)] hover:bg-[var(--primary-hover)] hover:text-white transition-colors shadow-lg hover:shadow-xl transform hover:-translate-y-0.5 transition-transform"
              >
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <Link
                to="/docs"
                className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-medium rounded-lg text-[var(--text-primary)] bg-white hover:bg-[var(--surface-bg)] transition-colors shadow"
              >
                Learn More
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Features */}
      <div className="py-12 bg-[var(--card-bg)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-[var(--text-primary)] sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-[var(--text-secondary)]">
              Everything you need to validate and visualize your requirements
            </p>
          </div>

          <div className="mt-16">
            <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature, index) => (
                <div key={index} className="pt-6 h-full">
                  <div className="h-full flex flex-col bg-[var(--content-bg)] rounded-lg px-6 pb-8 shadow-sm border border-[var(--card-border)]">
                    <div className="flex-grow">
                      <div className="inline-flex items-center justify-center p-3 bg-[var(--primary-main)] text-white rounded-md shadow-sm">
                        {feature.icon}
                      </div>
                      <h3 className="mt-6 text-lg font-medium text-[var(--text-primary)] tracking-tight">{feature.title}</h3>
                      <p className="mt-4 text-base text-[var(--text-secondary)] flex-grow">
                        {feature.description}
                      </p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-[var(--content-bg)]">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-[var(--primary-main)] to-[var(--primary-hover)] rounded-2xl shadow-xl overflow-hidden">
            <div className="px-6 py-12 sm:px-16 lg:py-16 lg:px-24">
              <div className="text-center lg:text-left lg:flex lg:items-center lg:justify-between">
                <div className="mb-8 lg:mb-0">
                  <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
                    <span className="block">Ready to Transform Your Requirements Process?</span>
                  </h2>
                  <p className="mt-4 text-lg text-[var(--primary-50)] max-w-2xl">
                    Join thousands of teams who trust VisSpec for their requirements validation and visualization needs.
                  </p>
                </div>
                <Link
                  to="/login"
                  className="inline-block bg-white text-[var(--primary-main)] font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-[var(--primary-50)] transition-colors transform hover:scale-105 transition-transform"
                >
                  Start Free Trial
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-[var(--card-bg)] border-t border-[var(--card-border)]">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center">
              <Brain className="h-6 w-6 text-[var(--primary-main)]" />
              <span className="ml-2 text-lg font-bold text-[var(--text-primary)]">VisSpec</span>
            </div>
            <div className="mt-4 md:mt-0 flex space-x-6">
              <a href="#" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                <Github className="h-6 w-6" />
              </a>
              <a href="#" className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]">
                <BookOpen className="h-6 w-6" />
              </a>
            </div>
          </div>
          <div className="mt-8 text-center text-sm text-[var(--text-secondary)]">
            <p>© {new Date().getFullYear()} VisSpec. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;