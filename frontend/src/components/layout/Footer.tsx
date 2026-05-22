'use client';

import { usePathname } from 'next/navigation';

export function Footer() {
  const pathname = usePathname();

  // Don't show footer on login/signup pages
  if (pathname === '/login' || pathname === '/signup') {
    return null;
  }

  return (
    <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
      <div className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-3 gap-8">
          <div>
            <h3 className="font-bold text-lg mb-4">GYMPT</h3>
            <p className="text-gray-600 text-sm">
              AI-powered personal fitness trainer with real-time posture analysis
            </p>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li>
                <a href="/about" className="hover:text-blue-600">About</a>
              </li>
              <li>
                <a href="/features" className="hover:text-blue-600">Features</a>
              </li>
              <li>
                <a href="/privacy" className="hover:text-blue-600">Privacy Policy</a>
              </li>
              <li>
                <a href="/terms" className="hover:text-blue-600">Terms of Service</a>
              </li>
            </ul>
          </div>

          <div>
            <h4 className="font-semibold mb-4">Contact</h4>
            <p className="text-gray-600 text-sm">
              Email: support@gympt.com<br />
              Version: 0.1.0
            </p>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-gray-200 text-center text-sm text-gray-600">
          &copy; 2024 GYMPT. All rights reserved.
        </div>
      </div>
    </footer>
  );
}
