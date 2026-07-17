'use client';

import { useState } from 'react';
import { AlertTriangle, Search, HardHat, FileText, CheckCircle, XCircle, AlertCircle, Shield, Eye, Bell, Ban } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { cn, formatDate } from '@/lib/utils';

interface SafetyIncident {
  id: string;
  title: string;
  type: 'near_miss' | 'safety_observation' | 'incident' | 'violation';
  severity: 'critical' | 'high' | 'medium' | 'low';
  status: 'open' | 'investigating' | 'resolved' | 'closed';
  location: string;
  reported_by: string;
  reported_date: string;
  description: string;
  actions_taken?: string;
}

const mockIncidents: SafetyIncident[] = [
  { id: 'SI-2024-001', title: 'Unsecured ladder in Pump House A', type: 'safety_observation', severity: 'medium', status: 'resolved', location: 'Pump House A', reported_by: 'Safety Officer', reported_date: '2026-07-12', description: 'Ladder was left unsecured near Pump P-102 after maintenance work', actions_taken: 'Ladder secured, worker reminded of safety protocol' },
  { id: 'SI-2024-002', title: 'Confined space entry without permit', type: 'violation', severity: 'critical', status: 'investigating', location: 'Tank TK-201', reported_by: 'Shift Supervisor', reported_date: '2026-07-11', description: 'Worker entered confined space without gas test or permit' },
  { id: 'SI-2024-003', title: 'Oil spill near Compressor C-402', type: 'incident', severity: 'high', status: 'open', location: 'Compressor Area', reported_by: 'Mike R.', reported_date: '2026-07-10', description: 'Approximately 5L of oil leaked from compressor seal' },
  { id: 'SI-2024-004', title: 'Missing guard on rotating shaft - IDF-201', type: 'safety_observation', severity: 'high', status: 'open', location: 'Boiler Area', reported_by: 'Safety Inspector', reported_date: '2026-07-09', description: 'Shaft coupling guard missing on Induced Draft Fan' },
  { id: 'SI-2024-005', title: 'Worker slipped on wet floor in Turbine Hall', type: 'near_miss', severity: 'medium', status: 'resolved', location: 'Turbine Hall', reported_by: 'Operations', reported_date: '2026-07-08', description: 'No injury but could have been serious', actions_taken: 'Floor cleaned, anti-slip mats installed' },
  { id: 'SI-2024-006', title: 'Fire extinguisher access blocked - Switchyard', type: 'violation', severity: 'critical', status: 'closed', location: 'Switchyard', reported_by: 'Safety Audit', reported_date: '2026-07-07', description: 'Fire extinguisher obstructed by stored materials', actions_taken: 'Materials removed, area cleared' },
  { id: 'SI-2024-007', title: 'Hearing protection not worn in Boiler area', type: 'near_miss', severity: 'low', status: 'resolved', location: 'Boiler Area', reported_by: 'Safety Officer', reported_date: '2026-07-06', description: 'Worker found without earplugs in high-noise area', actions_taken: 'Verbal warning, refresher training scheduled' },
];

export default function SafetyPage() {
  const [incidents, setIncidents] = useState<SafetyIncident[]>(mockIncidents);
  const [searchQuery, setSearchQuery] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [severityFilter, setSeverityFilter] = useState('');

  const filtered = incidents.filter(item => {
    if (searchQuery && !item.title.toLowerCase().includes(searchQuery.toLowerCase()) && !item.location.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    if (typeFilter && item.type !== typeFilter) return false;
    if (statusFilter && item.status !== statusFilter) return false;
    if (severityFilter && item.severity !== severityFilter) return false;
    return true;
  });

  const stats = {
    total: incidents.length,
    open: incidents.filter(i => i.status === 'open').length,
    investigating: incidents.filter(i => i.status === 'investigating').length,
    critical: incidents.filter(i => i.severity === 'critical').length,
    resolved: incidents.filter(i => i.status === 'resolved' || i.status === 'closed').length,
  };

  const getSeverityColor = (s: SafetyIncident['severity']) => {
    const colors = { critical: 'bg-red-100 text-red-700', high: 'bg-orange-100 text-orange-700', medium: 'bg-yellow-100 text-yellow-700', low: 'bg-green-100 text-green-700' };
    return colors[s];
  };

  const getStatusColor = (s: SafetyIncident['status']) => {
    const colors = { open: 'bg-red-100 text-red-700', investigating: 'bg-yellow-100 text-yellow-700', resolved: 'bg-blue-100 text-blue-700', closed: 'bg-green-100 text-green-700' };
    return colors[s];
  };

  const getTypeIcon = (t: SafetyIncident['type']) => {
    const icons = { near_miss: 'bg-orange-100 text-orange-700', safety_observation: 'bg-blue-100 text-blue-700', incident: 'bg-red-100 text-red-700', violation: 'bg-purple-100 text-purple-700' };
    return icons[t];
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Safety</h1>
              <p className="text-gray-500">Incident reporting, safety observations, and hazard tracking</p>
            </div>
            <Button>
              <AlertTriangle className="h-4 w-4 mr-2" />
              Report Incident
            </Button>
          </div>
        </div>
      </header>

      <div className="max-w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Total Reports</p><p className="text-3xl font-bold text-gray-900">{stats.total}</p></div><HardHat className="h-10 w-10 text-primary-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Open</p><p className="text-3xl font-bold text-red-600">{stats.open}</p></div><AlertCircle className="h-10 w-10 text-red-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Investigating</p><p className="text-3xl font-bold text-yellow-600">{stats.investigating}</p></div><Shield className="h-10 w-10 text-yellow-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Critical</p><p className="text-3xl font-bold text-red-600">{stats.critical}</p></div><Ban className="h-10 w-10 text-red-600" /></div></CardContent></Card>
          <Card><CardContent className="p-6"><div className="flex items-center justify-between"><div><p className="text-sm text-gray-500">Resolved</p><p className="text-3xl font-bold text-green-600">{stats.resolved}</p></div><CheckCircle className="h-10 w-10 text-green-600" /></div></CardContent></Card>
        </div>

        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-center">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input placeholder="Search safety reports..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} className="pl-10" />
              </div>
              <Select value={typeFilter} onValueChange={setTypeFilter}>
                <SelectTrigger className="w-[170px]"><SelectValue placeholder="Type" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Types</SelectItem>
                  <SelectItem value="near_miss">Near Miss</SelectItem>
                  <SelectItem value="safety_observation">Observation</SelectItem>
                  <SelectItem value="incident">Incident</SelectItem>
                  <SelectItem value="violation">Violation</SelectItem>
                </SelectContent>
              </Select>
              <Select value={severityFilter} onValueChange={setSeverityFilter}>
                <SelectTrigger className="w-[140px]"><SelectValue placeholder="Severity" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Severity</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  <SelectItem value="open">Open</SelectItem>
                  <SelectItem value="investigating">Investigating</SelectItem>
                  <SelectItem value="resolved">Resolved</SelectItem>
                  <SelectItem value="closed">Closed</SelectItem>
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
                  <TableHead>ID</TableHead>
                  <TableHead>Report</TableHead>
                  <TableHead>Type</TableHead>
                  <TableHead>Severity</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Reported</TableHead>
                  <TableHead>Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filtered.map(item => (
                  <TableRow key={item.id} className="hover:bg-gray-50">
                    <TableCell><span className="text-sm font-mono font-medium">{item.id}</span></TableCell>
                    <TableCell>
                      <p className="text-sm font-medium">{item.title}</p>
                      <p className="text-xs text-gray-500">{item.description}</p>
                    </TableCell>
                    <TableCell><Badge variant="secondary" className={getTypeIcon(item.type)}>{item.type.replace('_', ' ')}</Badge></TableCell>
                    <TableCell><Badge variant="secondary" className={getSeverityColor(item.severity)}>{item.severity}</Badge></TableCell>
                    <TableCell><Badge variant="secondary" className={getStatusColor(item.status)}>{item.status}</Badge></TableCell>
                    <TableCell className="text-sm">{item.location}</TableCell>
                    <TableCell className="text-sm">
                      <p>{item.reported_by}</p>
                      <p className="text-xs text-gray-500">{item.reported_date}</p>
                    </TableCell>
                    <TableCell>
                      <div className="flex gap-1">
                        <Button variant="ghost" size="icon" className="h-7 w-7"><Eye className="h-4 w-4" /></Button>
                        <Button variant="ghost" size="icon" className="h-7 w-7"><Bell className="h-4 w-4" /></Button>
                      </div>
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