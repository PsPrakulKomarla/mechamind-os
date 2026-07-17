'use client';

import { useState } from 'react';
import { ShieldCheck, Search, AlertTriangle, CheckCircle, XCircle, FileText, ExternalLink, Calendar } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn } from '@/lib/utils';

interface ComplianceItem {
  id: string;
  regulation: string;
  title: string;
  status: 'compliant' | 'gap' | 'non_compliant' | 'pending';
  equipment: string;
  area: string;
  due_date: string;
  severity: 'high' | 'medium' | 'low';
  description: string;
}

const mockCompliance: ComplianceItem[] = [
  { id: 'C-001', regulation: 'OISD-116', title: 'Fire Protection System - Pressure Vessels', status: 'compliant', equipment: 'Boiler B-601', area: 'Unit 1 - Power Block', due_date: '2026-08-01', severity: 'high', description: 'Fire suppression system inspection for pressure vessels' },
  { id: 'C-002', regulation: 'OISD-116', title: 'Emergency Shutdown System Testing', status: 'gap', equipment: 'Main Steam Valve V-301', area: 'Unit 1 - Turbine Hall', due_date: '2026-07-20', severity: 'high', description: 'ESD system functional test overdue' },
  { id: 'C-003', regulation: 'ISO 14224', title: 'Equipment Classification & Taxonomy', status: 'compliant', equipment: 'All Assets', area: 'Plant-wide', due_date: '2026-09-15', severity: 'medium', description: 'Equipment classification standards compliance' },
  { id: 'C-004', regulation: 'OISD-105', title: 'Electrical Safety - Grounding Inspection', status: 'non_compliant', equipment: 'Transformer TRF-901', area: 'Switchyard', due_date: '2026-07-10', severity: 'high', description: 'Grounding resistance exceeds permissible limit' },
  { id: 'C-005', regulation: 'EPA-40CFR60', title: 'Emissions Monitoring - Continuous', status: 'pending', equipment: 'Stack Monitoring System', area: 'Environmental', due_date: '2026-08-30', severity: 'medium', description: 'Quarterly emissions report pending submission' },
  { id: 'C-006', regulation: 'ISO 45001', title: 'Worker Safety - Confined Space Entry', status: 'compliant', equipment: 'All Vessels', area: 'Plant-wide', due_date: '2026-10-01', severity: 'high', description: 'Confined space entry procedures and training' },
  { id: 'C-007', regulation: 'OISD-118', title: 'Storage Tank Integrity - TK-201', status: 'gap', equipment: 'Storage Tank TK-201', area: 'Tank Farm', due_date: '2026-07-25', severity: 'high', description: 'Ultrasonic thickness testing overdue by 30 days' },
];

const regulations = ['OISD-116', 'OISD-105', 'OISD-118', 'ISO 14224', 'ISO 45001', 'EPA-40CFR60'];

export default function CompliancePage() {
  const [items, setItems] = useState<ComplianceItem[]>(mockCompliance);
  const [searchQuery, setSearchQuery] = useState('');
  const [regulationFilter, setRegulationFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');

  const filtered = items.filter(item => {
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase()) && !item.regulation.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (regulationFilter && item.regulation !== regulationFilter) return false;
    if (statusFilter && item.status !== statusFilter) return false;
    return true;
  });

  const stats = {
    total: items.length,
    compliant: items.filter(i => i.status === 'compliant').length,
    gap: items.filter(i => i.status === 'gap').length,
    nonCompliant: items.filter(i => i.status === 'non_compliant').length,
    overdue: items.filter(i => new Date(i.due_date) < new Date() && i.status !== 'compliant').length,
  };

  const getStatusBadge = (status: ComplianceItem['status']) => {
    const colors = { compliant: 'bg-green-100 text-green-700', gap: 'bg-yellow-100 text-yellow-700', non_compliant: 'bg-red-100 text-red-700', pending: 'bg-gray-100 text-gray-700' };
    return <Badge variant="secondary" className={colors[status]}>{status.replace('_', ' ')}</Badge>;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Compliance</h1>
              <p className="text-gray-500">Regulatory compliance tracking, audits, and gap analysis</p>
            </div>
            <Button variant="outline">
              <FileText className="h-4 w-4 mr-2" />
              Generate Audit Report
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Total Items</p><p className="text-3xl font-bold text-gray-900">{stats.total}</p></div><ShieldCheck className="h-10 w-10 text-primary-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Compliant</p><p className="text-3xl font-bold text-green-600">{stats.compliant}</p></div><CheckCircle className="h-10 w-10 text-green-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Gaps</p><p className="text-3xl font-bold text-yellow-600">{stats.gap}</p></div><AlertTriangle className="h-10 w-10 text-yellow-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Non-Compliant</p><p className="text-3xl font-bold text-red-600">{stats.nonCompliant}</p></div><XCircle className="h-10 w-10 text-red-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Overdue</p><p className="text-3xl font-bold text-red-600">{stats.overdue}</p></div><Calendar className="h-10 w-10 text-red-600" /></div></CardContent></Card>
        </div>

        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input placeholder="Search compliance items..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
              <Select value={regulationFilter} onValueChange={setRegulationFilter}>
                <SelectTrigger className="w-[160px]"><SelectValue placeholder="Regulation" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Regulations</SelectItem>
                  {regulations.map(r => <SelectItem key={r} value={r}>{r}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="compliant">Compliant</SelectItem>
                  <SelectItem value="gap">Gap</SelectItem>
                  <SelectItem value="non_compliant">Non-Compliant</SelectItem>
                  <SelectItem value="pending">Pending</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardContent className="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Regulation</TableHead>
                  <TableHead>Requirement</TableHead>
                  <TableHead>Equipment</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(item => (
                  <TableRow key={item.id} className="hover:bg-gray-50">
                    <TableCell><Badge variant="secondary" className="bg-purple-100 text-purple-700">{item.regulation}</Badge></TableCell>
                    <TableCell>
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-xs text-gray-500">{item.description}</p>
                    </TableCell>
                    <TableCell className="text-sm">{item.equipment}</TableCell>
                    <TableCell>{getStatusBadge(item.status)}</TableCell>
                    <TableCell>
                      <Badge variant="secondary" className={cn(item.severity === 'high' ? 'bg-red-100 text-red-700' : item.severity === 'medium' ? 'bg-yellow-100 text-yellow-700' : 'bg-green-100 text-green-700')}>{item.severity}</Badge>
                    </TableCell>
                    <TableCell className={cn('text-sm font-mono', new Date(item.due_date) < new Date() && item.status !== 'compliant' ? 'text-red-600 font-bold' : '')}>{item.due_date}</TableCell>
                    <TableCell>
                      <Button variant="ghost" size="icon" className="h-7 w-7"><ExternalLink className="h-4 w-4" /></Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}