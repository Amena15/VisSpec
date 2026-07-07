import React from 'react';
import {
  ArrowRight,
  Zap,
  BarChart3,
  Users,
  FileText,
  Github,
  BookOpen,
  Brain,
  Upload,
  CheckCircle,
  GitBranch,
  PlayCircle,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const LandingPage = () => {
  const features = [
    {
      title: 'AI-Powered Analysis',
      description:
        'Automatically detect ambiguities, contradictions, and inconsistencies in your requirements using LLMs.',
      icon: <Zap className="h-6 w-6" />,
    },
    {
      title: 'Visual Traceability',
      description:
        'Link requirements to generated UML diagrams and track changes throughout the lifecycle.',
      icon: <BarChart3 className="h-6 w-6" />,
    },
    {
      title: 'Role-Based Access',
      description:
        'Dedicated interfaces for analysts and supervisors with appropriate permissions and workflows.',
      icon: <Users className="h-6 w-6" />,
    },
    {
      title: 'Document Validation',
      description:
        'Ensure your SRS documents meet IEEE 830 standards and best practices with semantic checks.',
      icon: <FileText className="h-6 w-6" />,
    },
  ];

  const workflowSteps = [
    { icon: Upload, label: 'Upload SRS', desc: 'PDF, DOCX, or TXT' },
    { icon: Brain, label: 'AI Validation', desc: 'LLaMA 3 semantic analysis' },
    { icon: GitBranch, label: 'Traceability', desc: 'Requirements → Diagrams' },
    { icon: CheckCircle, label: 'Export Report', desc: 'PDF with insights' },
  ];

  return (
    <div className="min-h-screen bg-[var(--content-bg)]">
      {/* Navigation */}
      <nav className="bg-[var(--card-bg)]/80 backdrop-blur-sm border-b border-[var(--card-border)] sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between h-16">
            <div className="flex items-center">
              <Brain className="h-8 w-8 text-[var(--primary-main)]" />
              <span className="ml-2 text-xl font-bold text-[var(--text-primary)]">VisSpec</span>
            </div>
            <div className="flex items-center space-x-4">
              <a
                href="https://mmuedumy-my.sharepoint.com/personal/1221305728_student_mmu_edu_my/_layouts/15/stream.aspx?id=%2Fpersonal%2F1221305728%5Fstudent%5Fmmu%5Fedu%5Fmy%2FDocuments%2F1221305728%5FDrZarinaCheEmbi%5FFYP2%5FPresentationVideo%2Emp4&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E673a6003%2D1793%2D43c5%2D9868%2D77b1c53ca510"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-[var(--text-secondary)] hover:text-[var(--primary-main)] transition-colors"
              >
                <PlayCircle className="h-5 w-5 mr-1" />
                <span className="text-sm font-medium">Watch Demo</span>
              </a>
              <Link
                to="/login"
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3 py-2 rounded-md text-sm font-medium transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/login"
                className="bg-[var(--primary-main)] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[var(--primary-hover)] hover:text-white transition-all shadow-md hover:shadow-lg"
              >
                Get Started
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Enhanced Background */}
      <section className="relative overflow-hidden bg-gradient-to-br from-[var(--content-bg)] via-[var(--surface-bg)] to-[var(--card-bg)]">
        {/* Animated gradient orbs - no lines */}
        <div className="absolute inset-0 pointer-events-none">
          <div className="absolute top-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-[var(--primary-main)]/10 blur-3xl animate-float" />
          <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] rounded-full bg-[var(--primary-hover)]/10 blur-3xl animate-float animation-delay-1000" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[70%] h-[70%] rounded-full bg-[var(--primary-main)]/5 blur-3xl animate-pulse-slow" />
        </div>

        {/* Subtle mesh gradient overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--primary-main)_0%,_transparent_70%)] opacity-[0.03] pointer-events-none" />

        <div className="relative max-w-7xl mx-auto py-24 px-4 sm:py-32 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center justify-center p-3 bg-[var(--primary-main)]/10 rounded-full mb-6 animate-fade-in">
              <Brain className="h-12 w-12 text-[var(--primary-main)]" />
            </div>
            <h1 className="text-4xl tracking-tight font-extrabold text-[var(--text-primary)] sm:text-5xl md:text-6xl animate-fade-in-up">
              <span className="block">AI-Powered Requirements</span>
              <span className="block text-[var(--primary-main)] mt-2">Validation & Visualization</span>
            </h1>
            <p className="mt-6 max-w-lg mx-auto text-lg text-[var(--text-secondary)] sm:max-w-3xl animate-fade-in-up animation-delay-200">
              Transform your SRS documents into validated, visual specifications with AI-driven analysis
              and comprehensive traceability.
            </p>
            <div className="mt-10 flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4 animate-fade-in-up animation-delay-400">
              <Link
                to="/login"
                className="inline-flex items-center justify-center px-8 py-4 border border-transparent text-base font-medium rounded-lg text-white bg-[var(--primary-main)] hover:bg-[var(--primary-hover)] hover:text-white transition-all shadow-lg hover:shadow-xl transform hover:-translate-y-0.5"
              >
                Get Started
                <ArrowRight className="ml-2 h-5 w-5" />
              </Link>
              <a
                href="#workflow"
                className="inline-flex items-center justify-center px-8 py-4 border border-[var(--card-border)] text-base font-medium rounded-lg text-[var(--text-primary)] bg-white hover:bg-[var(--surface-bg)] transition-all shadow-sm hover:shadow"
              >
                See How It Works
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Workflow Section */}
      <section id="workflow" className="py-16 bg-[var(--card-bg)] border-y border-[var(--card-border)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-extrabold text-[var(--text-primary)] sm:text-4xl">
              How VisSpec Works
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-[var(--text-secondary)]">
              From document upload to validated insights – a seamless workflow
            </p>
          </div>
          <div className="grid grid-cols-1 gap-8 md:grid-cols-2 lg:grid-cols-4">
            {workflowSteps.map((step, idx) => (
              <div key={idx} className="relative flex flex-col items-center text-center group">
                <div className="flex items-center justify-center w-16 h-16 rounded-full bg-[var(--primary-main)]/10 text-[var(--primary-main)] group-hover:bg-[var(--primary-main)] group-hover:text-white transition-colors duration-300">
                  <step.icon className="h-8 w-8" />
                </div>
                <h3 className="mt-4 text-lg font-medium text-[var(--text-primary)]">{step.label}</h3>
                <p className="mt-1 text-sm text-[var(--text-secondary)]">{step.desc}</p>
                {idx < workflowSteps.length - 1 && (
                  <div className="hidden lg:block absolute top-8 left-[calc(50%+3rem)] w-[calc(100%-3rem)] h-0.5 bg-[var(--card-border)] group-hover:bg-[var(--primary-main)]/50 transition-colors" />
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="py-16 bg-[var(--content-bg)]">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <h2 className="text-3xl font-extrabold text-[var(--text-primary)] sm:text-4xl">
              Powerful Features
            </h2>
            <p className="mt-4 max-w-2xl mx-auto text-xl text-[var(--text-secondary)]">
              Everything you need to validate and visualize your requirements
            </p>
          </div>
          <div className="mt-16 grid grid-cols-1 gap-8 sm:grid-cols-2 lg:grid-cols-4">
            {features.map((feature, index) => (
              <div
                key={index}
                className="group relative bg-[var(--card-bg)] rounded-xl p-6 shadow-sm border border-[var(--card-border)] hover:shadow-lg hover:-translate-y-1 transition-all duration-200"
              >
                <div className="inline-flex items-center justify-center p-3 bg-[var(--primary-main)]/10 text-[var(--primary-main)] rounded-lg group-hover:bg-[var(--primary-main)] group-hover:text-white transition-colors">
                  {feature.icon}
                </div>
                <h3 className="mt-4 text-lg font-medium text-[var(--text-primary)]">{feature.title}</h3>
                <p className="mt-2 text-base text-[var(--text-secondary)]">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-[var(--content-bg)]">
        <div className="max-w-7xl mx-auto py-16 px-4 sm:px-6 lg:px-8">
          <div className="bg-gradient-to-r from-[var(--primary-main)] to-[var(--primary-hover)] rounded-2xl shadow-xl overflow-hidden">
            <div className="px-6 py-12 sm:px-16 lg:py-16 lg:px-24">
              <div className="text-center lg:text-left lg:flex lg:items-center lg:justify-between">
                <div className="mb-8 lg:mb-0">
                  <h2 className="text-3xl font-extrabold text-white sm:text-4xl">
                    <span className="block">Ready to Transform Your Requirements Process?</span>
                  </h2>
                  <p className="mt-4 text-lg text-[var(--primary-50)] max-w-2xl">
                    Join teams that trust VisSpec for validation, visualization, and traceability.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row space-y-3 sm:space-y-0 sm:space-x-4">
                  <Link
                    to="/login"
                    className="inline-flex items-center justify-center bg-white text-[var(--primary-main)] font-bold px-8 py-4 rounded-lg shadow-lg hover:bg-[var(--primary-50)] transition-colors transform hover:scale-105"
                  >
                    Start Free Trial
                    <ArrowRight className="ml-2 h-5 w-5" />
                  </Link>
                  <a
                    href="https://mmuedumy-my.sharepoint.com/personal/1221305728_student_mmu_edu_my/_layouts/15/stream.aspx?id=%2Fpersonal%2F1221305728%5Fstudent%5Fmmu%5Fedu%5Fmy%2FDocuments%2F1221305728%5FDrZarinaCheEmbi%5FFYP2%5FPresentationVideo%2Emp4&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E673a6003%2D1793%2D43c5%2D9868%2D77b1c53ca510"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center bg-white/20 backdrop-blur-sm text-white font-medium px-8 py-4 rounded-lg border border-white/30 hover:bg-white/30 transition-colors"
                  >
                    <PlayCircle className="mr-2 h-5 w-5" />
                    Watch Demo Video
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-[var(--card-bg)] border-t border-[var(--card-border)]">
        <div className="max-w-7xl mx-auto py-8 px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex items-center">
              <Brain className="h-6 w-6 text-[var(--primary-main)]" />
              <span className="ml-2 text-lg font-bold text-[var(--text-primary)]">VisSpec</span>
            </div>
            <div className="mt-4 md:mt-0 flex space-x-6">
              <a
                href="https://github.com/Amena15/VisSpec/tree/production3"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                aria-label="GitHub"
              >
                <Github className="h-6 w-6" />
              </a>
              <a
                href="https://mmuedumy-my.sharepoint.com/personal/1221305728_student_mmu_edu_my/_layouts/15/stream.aspx?id=%2Fpersonal%2F1221305728%5Fstudent%5Fmmu%5Fedu%5Fmy%2FDocuments%2F1221305728%5FDrZarinaCheEmbi%5FFYP2%5FPresentationVideo%2Emp4&referrer=StreamWebApp%2EWeb&referrerScenario=AddressBarCopied%2Eview%2E673a6003%2D1793%2D43c5%2D9868%2D77b1c53ca510"
                target="_blank"
                rel="noopener noreferrer"
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                aria-label="Video Demo"
              >
                <PlayCircle className="h-6 w-6" />
              </a>
              <a
                href="#"
                className="text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors"
                aria-label="Documentation"
              >
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