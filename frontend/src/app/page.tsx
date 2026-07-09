'use client';

import { useState } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import {
  LayoutDashboard,
  MessageSquare,
  Search,
  Settings,
  Building2,
  Wrench,
  ShieldCheck,
  AlertTriangle,
  FileText,
  Upload,
  Zap,
  Brain,
  HardHat,
  Database,
  ChevronRight,
  Menu,
  X,
  Bell,
  User,
  LogOut,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

const navigation = [
  { name: 'Dashboard', href: '/', icon: LayoutDashboard },
  { name: 'Knowledge Copilot', href: '/chat', icon: MessageSquare },
  { name: 'Smart Search', href: '/search', icon: Search },
  { name: 'Equipment Registry', href: '/equipment', icon: Building2 },
  { name: 'Maintenance', href: '/maintenance', icon: Wrench },
  { name: 'Compliance', href: '/compliance', icon: ShieldCheck },
  { name: 'Safety', href: '/safety', icon: AlertTriangle },
];

const stats = [
  { label: 'Documents', value: '1,247', change: '+12%', icon: FileText },
  { label: 'Equipment', value: '89', change: '+3', icon: Building2 },
  { label: 'Open Issues', value: '23', change: '-5', icon: AlertTriangle },
  { label: 'Compliance Rate', value: '94%', change: '+2%', icon: ShieldCheck },
];

export default function DashboardPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (searchQuery.trim()) {
      router.push(`/search?q=${encodeURIComponent(searchQuery)}`);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          'fixed inset-y-0 left-0 z-50 w-64 bg-white border-r border-gray-200 transform transition-transform duration-300 lg:translate-x-0',
          sidebarOpen ? 'translate-x-0' : '-translate-x-full'
        )}
      >
        <div className="flex h-16 items-center justify-between px-4 border-b border-gray-200">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-primary-600 flex items-center justify-center">
              <Zap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl text-gray-900">Mechamind OS</span>
          </div>
          <button
            className="lg:hidden p-2 rounded-md hover:bg-gray-100"
            onClick={() => setSidebarOpen(false)}
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <nav className="p-4 space-y-1" role="navigation" aria-label="Main navigation">
          {navigation.map((item) => {
            const isActive = searchParams.get('page') === item.href || 
              (item.href === '/' && !searchParams.get('page'));
            return (
              <Link
                key={item.name}
                href={item.href}
                className={cn(
                  'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-primary-50 text-primary-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                )}
              >
                <item.icon className="w-5 h-5" aria-hidden="true" />
                {item.name}
              </Link>
            );
          })}
        </nav>

        <div className="absolute bottom-0 left-0 right-0 p-4 border-t border-gray-200">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-gray-200" />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">John Engineer</p>
              <p className="text-xs text-gray-500 truncate">Senior Maintenance Engineer</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="lg:pl-64">
        {/* Top bar */}
        <header className="sticky top-0 z-30 bg-white border-b border-gray-200">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            <div className="flex items-center gap-4">
              <button
                className="lg:hidden p-2 rounded-md hover:bg-gray-100"
                onClick={() => setSidebarOpen(true)}
                aria-label="Open menu"
              >
                <Menu className="w-6 h-6" />
              </button>

              <form onSubmit={handleSearch} className="hidden sm:block relative w-80 md:w-96">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <Input
                  type="search"
                  placeholder="Search equipment, documents, procedures..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  aria-label="Global search"
                />
              </form>
            </div>

            <div className="flex items-center gap-2">
              <Button variant="ghost" size="icon" className="relative">
                <Bell className="w-5 h-5" />
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 text-white text-xs rounded-full flex items-center justify-center">3</span>
              </Button>
              <div className="hidden sm:block w-px h-6 bg-gray-200" />
              <Button variant="ghost" size="icon">
                <User className="w-5 h-5" />
              </Button>
              <Button variant="ghost" size="icon">
                <LogOut className="w-5 h-5" />
              </Button>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <div className="mb-8">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Dashboard</h1>
            <p className="mt-1 text-gray-600">Overview of your industrial knowledge intelligence platform</p>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            {stats.map((stat) => (
              <div key={stat.label} className="bg-white rounded-xl border border-gray-200 p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-500">{stat.label}</p>
                    <p className="text-3xl font-bold text-gray-900 mt-1">{stat.value}</p>
                    <p className="text-sm text-green-600 mt-1">{stat.change} vs last month</p>
                  </div>
                  <div className="w-12 h-12 rounded-xl bg-primary-100 flex items-center justify-center">
                    <stat.icon className="w-6 h-6 text-primary-600" />
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
            <div className="lg:col-span-2">
              <div className="bg-white rounded-xl border border-gray-200 p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {[
                    { label: 'Ask Knowledge Copilot', href: '/chat', icon: Brain, color: 'bg-purple-100 text-purple-600', desc: 'Get instant answers from your documents' },
                    { label: 'Upload Documents', href: '/documents', icon: Upload, color: 'bg-blue-100 text-blue-600', desc: 'Add PDFs, drawings, spreadsheets' },
                    { label: 'Search Knowledge Base', href: '/search', icon: Search, color: 'bg-green-100 text-green-600', desc: 'Find procedures, specs, regulations' },
                    { label: 'View Equipment Registry', href: '/equipment', icon: Building2, color: 'bg-orange-100 text-orange-600', desc: 'Browse 89 registered assets' },
                    { label: 'Maintenance Dashboard', href: '/maintenance', icon: Wrench, color: 'bg-indigo-100 text-indigo-600', desc: 'View schedules, history, predictions' },
                    { label: 'Compliance Status', href: '/compliance', icon: ShieldCheck, color: 'bg-red-100 text-red-600', desc: 'Audit readiness & gaps' },
                  ].map((action) => (
                    <Link
                      key={action.label}
                      href={action.href}
                      className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors group"
                    >
                      <div className="flex items-start gap-3">
                        <div className={cn('w-10 h-10 rounded-lg flex items-center justify-center flex-shrink-0', action.color)}>
                          <action.icon className="w-5 h-5" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-gray-900 group-hover:text-primary-600">{action.label}</p>
                          <p className="text-sm text-gray-500 mt-0.5">{action.desc}</p>
                        </div>
                        <ChevronRight className="w-5 h-5 text-gray-400 flex-shrink-0" />
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="bg-white rounded-xl border border-gray-200 p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
                <Link href="/documents" className="text-sm text-primary-600 hover:underline">View all</Link>
              </div>
              <div className="space-y-3">
                {[
                  { type: 'document', label: 'Pump P-101 Maintenance Manual uploaded', time: '2 min ago', user: 'Sarah M.' },
                  { type: 'chat', label: 'Question: "Bearing replacement procedure for P-101"', time: '15 min ago', user: 'Mike R.' },
                  { type: 'maintenance', label: 'Work order WO-2024-045 completed', time: '1 hour ago', user: 'Tech Team' },
                  { type: 'compliance', label: 'OISD-116 gap identified for Tank TK-201', time: '3 hours ago', user: 'Compliance Bot' },
                  { type: 'equipment', label: 'New equipment registered: Compressor C-402', time: 'Yesterday', user: 'Admin' },
                ].map((activity, i) => (
                  <div key={i} className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50">
                    <div className="w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
                      <FileText className="w-4 h-4 text-gray-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-900">{activity.label}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{activity.time} • {activity.user}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Equipment Status Overview */}
          <div className="bg-white rounded-xl border border-gray-200 p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-lg font-semibold text-gray-900">Equipment Status Overview</h2>
              <Link href="/equipment" className="text-sm text-primary-600 hover:underline">View all 89 →</Link>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-gray-200 text-left text-sm text-gray-500">
                    <th className="pb-3 font-medium">Equipment</th>
                    <th className="pb-3 font-medium">Tag</th>
                    <th className="pb-3 font-medium">Area</th>
                    <th className="pb-3 font-medium">Criticality</th>
                    <th className="pb-3 font-medium">Status</th>
                    <th className="pb-3 font-medium">Next Maintenance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {[
                    { name: 'Boiler Feed Pump', tag: 'P-101', area: 'Unit 1 - Power Block', criticality: 'Critical', status: 'Operational', nextMaint: '2025-02-10' },
                    { name: 'Induced Draft Fan', tag: 'IDF-201', area: 'Unit 1 - Boiler', criticality: 'Critical', status: 'Warning', nextMaint: '2025-02-05' },
                    { name: 'Steam Turbine', tag: 'TG-301', area: 'Unit 1 - Turbine Hall', criticality: 'Critical', status: 'Operational', nextMaint: '2025-06-15' },
                    { name: 'Instrument Air Compressor', tag: 'C-401', area: 'Utilities', criticality: 'Major', status: 'Operational', nextMaint: '2025-02-01' },
                    { name: 'Main Step-up Transformer', tag: 'TRF-901', area: 'Switchyard', criticality: 'Critical', status: 'Operational', nextMaint: '2025-03-01' },
                  ].map((eq, i) => (
                    <tr key={i} className="hover:bg-gray-50">
                      <td className="py-3 font-medium text-gray-900">{eq.name}</td>
                      <td className="py-3 text-gray-600 font-mono">{eq.tag}</td>
                      <td className="py-3 text-gray-600">{eq.area}</td>
                      <td className="py-3">
                        <span className={cn(
                          'px-2 py-1 rounded-full text-xs font-medium',
                          eq.criticality === 'Critical' && 'bg-red-100 text-red-700',
                          eq.criticality === 'Major' && 'bg-orange-100 text-orange-700',
                          eq.criticality === 'Minor' && 'bg-gray-100 text-gray-700'
                        )}>
                          {eq.criticality}
                        </span>
                      </td>
                      <td className="py-3">
                        <span className={cn(
                          'px-2 py-1 rounded-full text-xs font-medium',
                          eq.status === 'Operational' && 'bg-green-100 text-green-700',
                          eq.status === 'Warning' && 'bg-yellow-100 text-yellow-700',
                          eq.status === 'Down' && 'bg-red-100 text-red-700',
                          eq.status === 'Maintenance' && 'bg-blue-100 text-blue-700',
                        )}>
                          {eq.status}
                        </span>
                      </td>
                      <td className="py-3 text-gray-600 font-mono text-sm">{eq.nextMaint}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
}