import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldAlert, 
  Video, 
  Smartphone, 
  Cpu, 
  Activity, 
  ChevronRight, 
  Fingerprint, 
  FileCheck2,
  Users
} from 'lucide-react';

const Landing = () => {
  return (
    <div className="min-h-screen bg-dark-950 bg-grid text-dark-50 flex flex-col justify-between overflow-x-hidden">
      {/* Top Header / Navigation */}
      <header className="fixed top-0 left-0 right-0 z-40 bg-dark-950/80 backdrop-blur-md border-b border-dark-900">
        <div className="max-w-7xl mx-auto flex h-16 items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <ShieldAlert className="h-8 w-8 text-brand-500" />
            <span className="text-xl font-extrabold tracking-tight bg-gradient-to-r from-brand-400 to-indigo-500 bg-clip-text text-transparent">
              InterviewGuard AI
            </span>
          </div>
          <div className="flex items-center gap-4">
            <Link to="/login" className="text-sm font-semibold text-dark-300 hover:text-dark-50 transition-colors">
              Sign In
            </Link>
            <Link to="/signup" className="flex items-center gap-1 bg-brand-600 hover:bg-brand-700 text-sm font-semibold px-4 py-2 rounded-lg transition-all glow-indigo">
              Get Started Free
              <ChevronRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 pt-32 pb-20">
        <div className="max-w-7xl mx-auto px-6 text-center space-y-12">
          {/* Main heading */}
          <div className="space-y-6 max-w-4xl mx-auto">
            <span className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-500/10 border border-brand-500/20 text-xs font-semibold text-brand-400">
              💡 Multimodal AI Recruiting Security
            </span>
            <h1 className="text-4xl md:text-6xl font-extrabold tracking-tight leading-tight md:leading-none">
              Guarantee Interview Integrity with{' '}
              <span className="bg-gradient-to-r from-brand-400 via-indigo-500 to-purple-600 bg-clip-text text-transparent">
                Real-Time AI Guarding
              </span>
            </h1>
            <p className="text-lg md:text-xl text-dark-300 max-w-2xl mx-auto font-light leading-relaxed">
              Detect deepfakes, track candidate eye-gaze, scan for unauthorized devices, and verify liveness in live video interviews. Clean, publication-grade academic and commercial compliance.
            </p>
          </div>

          {/* Call to action buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/signup" className="w-full sm:w-auto flex items-center justify-center gap-2 bg-brand-600 hover:bg-brand-700 font-bold px-8 py-4 rounded-xl text-base transition-all glow-indigo">
              Schedule First Interview
              <ChevronRight className="h-5 w-5" />
            </Link>
            <a href="#features" className="w-full sm:w-auto flex items-center justify-center gap-2 bg-dark-900 border border-dark-800 hover:bg-dark-800 font-semibold px-8 py-4 rounded-xl text-base transition-all">
              Explore Subsystems
            </a>
          </div>

          {/* Premium Preview Box */}
          <div className="relative max-w-5xl mx-auto rounded-2xl overflow-hidden border border-dark-800 bg-dark-900/40 p-4 glow-indigo">
            <div className="absolute inset-0 bg-gradient-to-t from-dark-950 via-transparent to-transparent z-10"></div>
            <div className="w-full aspect-[16/9] rounded-xl bg-dark-950 flex flex-col items-center justify-center border border-dark-800/80 p-8 text-center space-y-4">
              <ShieldAlert className="h-16 w-16 text-brand-500 animate-bounce" />
              <h3 className="text-2xl font-bold">Multimodal Assessment Interface</h3>
              <p className="text-sm text-dark-300 max-w-lg">
                Recruiters see active video feeds, instant deepfake classification probabilities, phone alerts, gaze tracking directions, and challenge checks combined into a single unified workspace.
              </p>
              <div className="flex gap-2">
                <span className="text-xs bg-dark-800 px-3 py-1 rounded-full border border-dark-700">YOLOv8 Phone</span>
                <span className="text-xs bg-dark-800 px-3 py-1 rounded-full border border-dark-700">MediaPipe Iris</span>
                <span className="text-xs bg-dark-800 px-3 py-1 rounded-full border border-dark-700">PyTorch Deepfake</span>
              </div>
            </div>
          </div>
        </div>

        {/* Feature section */}
        <section id="features" className="max-w-7xl mx-auto px-6 py-24 space-y-16">
          <div className="text-center space-y-4">
            <h2 className="text-3xl md:text-4xl font-bold">Comprehensive Protection Subsystems</h2>
            <p className="text-dark-300 max-w-lg mx-auto">Four real-time pipelines processing webcam streams in parallel to evaluate candidate integrity.</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {/* Feature 1 */}
            <div className="glass p-6 rounded-xl hover:border-brand-500/30 transition-all duration-300 space-y-4">
              <div className="h-10 w-10 flex items-center justify-center bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg">
                <Cpu className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Deepfake Detection</h3>
              <p className="text-sm text-dark-300 leading-relaxed">
                PyTorch-powered classification model scanning facial features frame-by-frame. Highly accurate against face swap, puppetry, and digital mask generation.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="glass p-6 rounded-xl hover:border-brand-500/30 transition-all duration-300 space-y-4">
              <div className="h-10 w-10 flex items-center justify-center bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg">
                <Fingerprint className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Liveness Verification</h3>
              <p className="text-sm text-dark-300 leading-relaxed">
                Tracks blinking intervals, head alignment vectors, and smile ratios using MediaPipe Face Mesh. Blocks print-outs and pre-recorded video injection.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="glass p-6 rounded-xl hover:border-brand-500/30 transition-all duration-300 space-y-4">
              <div className="h-10 w-10 flex items-center justify-center bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg">
                <Activity className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Eye Gaze Tracking</h3>
              <p className="text-sm text-dark-300 leading-relaxed">
                Monitors Iris offsets to identify if candidates look away to a second monitor, check cheat sheets, or receive offline assistance.
              </p>
            </div>

            {/* Feature 4 */}
            <div className="glass p-6 rounded-xl hover:border-brand-500/30 transition-all duration-300 space-y-4">
              <div className="h-10 w-10 flex items-center justify-center bg-brand-500/10 border border-brand-500/20 text-brand-400 rounded-lg">
                <Smartphone className="h-6 w-6" />
              </div>
              <h3 className="text-lg font-bold">Device Detection</h3>
              <p className="text-sm text-dark-300 leading-relaxed">
                YOLOv8 detector identifies smartphones and multiple handheld devices instantly. Triggers high-severity alarms in the recruiter feed.
              </p>
            </div>
          </div>
        </section>

        {/* Pricing Tiers (Mock SaaS Plan) */}
        <section className="max-w-7xl mx-auto px-6 py-12 space-y-16 border-t border-dark-900">
          <div className="text-center space-y-4">
            <h2 className="text-3xl font-bold">Flexible Plans</h2>
            <p className="text-dark-300">Choose the right fit for your recruiting needs.</p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {/* Free */}
            <div className="glass p-8 rounded-xl border border-dark-800 flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-dark-300">Starter</h3>
                <h4 className="text-3xl font-extrabold">$0</h4>
                <p className="text-xs text-dark-300">Perfect for exploring subsystems.</p>
                <ul className="text-sm space-y-2 pt-4">
                  <li>✓ 5 interviews/mo</li>
                  <li>✓ Deepfake verification</li>
                  <li>✓ standard logs</li>
                </ul>
              </div>
              <Link to="/signup" className="block text-center bg-dark-800 border border-dark-700 py-2.5 rounded-lg text-sm font-semibold mt-8 hover:bg-dark-700">Get Started</Link>
            </div>

            {/* Pro */}
            <div className="glass-indigo p-8 rounded-xl border border-brand-500/30 flex flex-col justify-between relative">
              <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-brand-600 text-[10px] font-bold tracking-widest px-3 py-1 rounded-full uppercase">Most Popular</span>
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-brand-400">Professional</h3>
                <h4 className="text-3xl font-extrabold">$149<span className="text-sm font-normal text-dark-300">/mo</span></h4>
                <p className="text-xs text-dark-300">Complete SaaS package.</p>
                <ul className="text-sm space-y-2 pt-4">
                  <li>✓ Unlimited interviews</li>
                  <li>✓ Multimodal logs</li>
                  <li>✓ PDF PDF reports</li>
                  <li>✓ WebRTC Video Calling</li>
                </ul>
              </div>
              <Link to="/signup" className="block text-center bg-brand-600 hover:bg-brand-700 py-2.5 rounded-lg text-sm font-bold mt-8 glow-indigo">Start Free Trial</Link>
            </div>

            {/* Enterprise */}
            <div className="glass p-8 rounded-xl border border-dark-800 flex flex-col justify-between">
              <div className="space-y-4">
                <h3 className="text-lg font-bold text-dark-300">Enterprise</h3>
                <h4 className="text-3xl font-extrabold">Custom</h4>
                <p className="text-xs text-dark-300">Custom solutions for big teams.</p>
                <ul className="text-sm space-y-2 pt-4">
                  <li>✓ Custom model fine-tuning</li>
                  <li>✓ SSO integration</li>
                  <li>✓ Dedicated servers</li>
                </ul>
              </div>
              <a href="mailto:support@interviewguard.ai" className="block text-center bg-dark-800 border border-dark-700 py-2.5 rounded-lg text-sm font-semibold mt-8 hover:bg-dark-700">Contact Sales</a>
            </div>
          </div>
        </section>
      </main>

      {/* Footer */}
      <footer className="border-t border-dark-900 bg-dark-950 py-10">
        <div className="max-w-7xl mx-auto px-6 flex flex-col md:flex-row items-center justify-between gap-6 text-sm text-dark-300">
          <p>&copy; 2026 InterviewGuard AI. All rights reserved.</p>
          <div className="flex gap-6">
            <Link to="/login" className="hover:text-dark-50">Support</Link>
            <Link to="/login" className="hover:text-dark-50">Terms</Link>
            <Link to="/login" className="hover:text-dark-50">Privacy Policy</Link>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Landing;
