'use client';

import { useState, useEffect } from 'react';
import { Building2, AlertTriangle, Wrench, Search, Filter, ChevronDown, ChevronUp, Plus, Edit, Trash2, Eye, Download, Settings, AlertCircle, CheckCircle, XCircle, TrendingUp, TrendingDown } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger, DialogFooter } from '@/components/ui/dialog';
import { cn } from '@/lib/utils';

interface Equipment {
  id: string;
  name: string;
  tag_number: string;
  category: string;
  criticality: 'critical' | 'major' | 'minor';
  status: 'operational' | 'warning' | 'down' | 'maintenance' | 'unknown';
  location: string;
  area: string;
  manufacturer?: string;
  model?: string;
  last_maintenance_date?: string;
  next_maintenance_date?: string;
}

const mockEquipment: Equipment[] = [
  {
    id: '1',
    name: 'Boiler Feed Pump',
    tag_number: 'P-101',
    category: 'pump',
    criticality: 'critical',
    status: 'operational',
    location: 'Boiler Feedwater Area',
    area: 'Unit 1 - Power Block',
    manufacturer: 'KSB',
    model: 'WKLN 150/5',
    last_maintenance_date: '2024-11-10',
    next_maintenance_date: '2025-02-10',
  },
  {
    id: '2',
    name: 'Induced Draft Fan',
    tag_number: 'IDF-201',
    category: 'fan',
    criticality: 'critical',
    status: 'warning',
    location: 'Boiler Area',
    area: 'Unit 1 - Power Block',
    manufacturer: 'Howden',
    model: 'BVF 45/28',
    last_maintenance_date: '2024-11-05',
    next_maintenance_date: '2025-02-05',
  },
  {
    id: '3',
    name: 'Steam Turbine',
    tag_number: 'TG-301',
    category: 'turbine',
    criticality: 'critical',
    status: 'operational',
    location: 'Turbine Hall',
    area: 'Unit 1 - Power Block',
    manufacturer: 'Siemens',
    model: 'SST-6000',
    last_maintenance_date: '2024-06-15',
    next_maintenance_date: '2025-06-15',
  },
  {
    id: '4',
    name: 'Instrument Air Compressor',
    tag_number: 'C-401',
    category: 'compressor',
    criticality: 'major',
    status: 'operational',
    location: 'Instrument Air Station',
    area: 'Utilities',
    manufacturer: 'Atlas Copco',
    model: 'GA 160 VSD',
    last_maintenance_date: '2024-11-01',
    next_maintenance_date: '2025-02-01',
  },
  {
    id: '5',
    name: 'Main Step-up Transformer',
    tag_number: 'TRF-901',
    category: 'transformer',
    criticality: 'critical',
    status: 'operational',
    location: 'Switchyard',
    area: 'Electrical',
    manufacturer: 'CGL',
    model: '315 MVA 400/21 kV',
    last_maintenance_date: '2024-03-01',
    next_maintenance_date: '2025-03-01',
  },
];

const categories = [
  'pump', 'compressor', 'boiler', 'turbine', 'heat_exchanger',
  'conveyor', 'valve', 'motor', 'generator', 'transformer',
  'vessel', 'piping', 'instrument', 'control_system', 'safety_system',
];

const criticalities = ['critical', 'major', 'minor'];
const statuses = ['operational', 'warning', 'down', 'maintenance', 'unknown'];

export default function EquipmentPage() {
  const [equipment, setEquipment] = useState<Equipment[]>(mockEquipment);
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [criticalityFilter, setCriticalityFilter] = useState<string>('');
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [sortField, setSortField] = useState<'name' | 'criticality' | 'status' | 'next_maintenance'>('criticality');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  const [selectedEquipment, setSelectedEquipment] = useState<Equipment | null>(null);
  const [isDialogOpen, setIsDialogOpen] = useState(false);
  const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
  const [formData, setFormData] = useState<Partial<Equipment>>({});

  const filteredEquipment = equipment
    .filter((eq) => {
      if (searchQuery && !eq.name.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !eq.tag_number?.toLowerCase().includes(searchQuery.toLowerCase()) &&
          !eq.location?.toLowerCase().includes(searchQuery.toLowerCase())) {
        return false;
      }
      if (categoryFilter && eq.category !== categoryFilter) return false;
      if (criticalityFilter && eq.criticality !== criticalityFilter) return false;
      if (statusFilter && eq.status !== statusFilter) return false;
      return true;
    })
    .sort((a, b) => {
      let aVal = a[sortField];
      let bVal = b[sortField];
      if (sortField === 'next_maintenance') {
        aVal = a.next_maintenance_date || '';
        bVal = b.next_maintenance_date || '';
      }
      if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
      return 0;
    });

  const stats = {
    total: equipment.length,
    critical: equipment.filter(e => e.criticality === 'critical').length,
    warning: equipment.filter(e => e.status === 'warning').length,
    down: equipment.filter(e => e.status === 'down').length,
    overdue: equipment.filter(e => 
      e.next_maintenance_date && new Date(e.next_maintenance_date) < new Date()
    ).length,
  };

  const handleSort = (field: typeof sortField) => {
    if (sortField === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortOrder('asc');
    }
  };

  const getStatusBadge = (status: Equipment['status']) => {
    const variants: Record<Equipment['status'], string> = {
      operational: 'bg-green-100 text-green-700',
      warning: 'bg-yellow-100 text-yellow-700',
      down: 'bg-red-100 text-red-700',
      maintenance: 'bg-blue-100 text-blue-700',
      unknown: 'bg-gray-100 text-gray-700',
    };
    return (
      <Badge variant="secondary" className={variants[status]}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    );
  };

  const getCriticalityBadge = (crit: Equipment['criticality']) => {
    const variants: Record<Equipment['criticality'], string> = {
      critical: 'bg-red-100 text-red-700',
      major: 'bg-orange-100 text-orange-700',
      minor: 'bg-gray-100 text-gray-700',
    };
    return (
      <Badge variant="secondary" className={variants[crit]}>
        {crit.charAt(0).toUpperCase() + crit.slice(1)}
      </Badge>
    );
  };

  const openCreateDialog = () => {
    setEditingEquipment(null);
    setFormData({
      name: '',
      tag_number: '',
      category: 'pump',
      criticality: 'minor',
      status: 'operational',
      location: '',
      area: '',
      manufacturer: '',
      model: '',
    });
    setIsDialogOpen(true);
  };

  const openEditDialog = (eq: Equipment) => {
    setEditingEquipment(eq);
    setFormData({ ...eq });
    setIsDialogOpen(true);
  };

  const handleSubmit = () => {
    if (editingEquipment) {
      setEquipment(prev => prev.map(e => e.id === editingEquipment.id ? { ...e, ...formData } : e));
    } else {
      const newEq: Equipment = {
        id: Date.now().toString(),
        ...formData as Equipment,
      };
      setEquipment(prev => [...prev, newEq]);
    }
    setIsDialogOpen(false);
  };

  const handleDelete = (id: string) => {
    if (confirm('Are you sure you want to delete this equipment?')) {
      setEquipment(prev => prev.filter(e => e.id !== id));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">Equipment Registry</h1>
              <p className="text-gray-500">Manage and monitor all industrial assets</p>
            </div>
            <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
              <DialogTrigger asChild>
                <Button onClick={openCreateDialog}>
                  <Plus className="h-4 w-4 mr-2" />
                  Add Equipment
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>{editingEquipment ? 'Edit Equipment' : 'Add New Equipment'}</DialogTitle>
                </DialogHeader>
                <div className="grid grid-cols-2 gap-4 py-4">
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Name *</label>
                    <Input
                      value={formData.name || ''}
                      onChange={(e) => setFormData({...formData, name: e.target.value})}
                      placeholder="e.g., Boiler Feed Pump"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Tag Number *</label>
                    <Input
                      value={formData.tag_number || ''}
                      onChange={(e) => setFormData({...formData, tag_number: e.target.value})}
                      placeholder="e.g., P-101"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Category *</label>
                    <Select value={formData.category || 'pump'} onValueChange={(v) => setFormData({...formData, category: v})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {categories.map(c => <SelectItem key={c} value={c}>{c.replace('_', ' ').toUpperCase()}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Criticality *</label>
                    <Select value={formData.criticality || 'minor'} onValueChange={(v) => setFormData({...formData, criticality: v as any})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {criticalities.map(c => <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Status</label>
                    <Select value={formData.status || 'operational'} onValueChange={(v) => setFormData({...formData, status: v as any})}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        {statuses.map(s => <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>)}
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Location</label>
                    <Input
                      value={formData.location || ''}
                      onChange={(e) => setFormData({...formData, location: e.target.value})}
                      placeholder="e.g., Boiler Feedwater Area"
                    />
                  </div>
                  <div className="col-span-2">
                    <label className="block text-sm font-medium mb-1">Area</label>
                    <Input
                      value={formData.area || ''}
                      onChange={(e) => setFormData({...formData, area: e.target.value})}
                      placeholder="e.g., Unit 1 - Power Block"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Manufacturer</label>
                    <Input
                      value={formData.manufacturer || ''}
                      onChange={(e) => setFormData({...formData, manufacturer: e.target.value})}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium mb-1">Model</label>
                    <Input
                      value={formData.model || ''}
                      onChange={(e) => setFormData({...formData, model: e.target.value})}
                    />
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsDialogOpen(false)}>Cancel</Button>
                  <Button onClick={handleSubmit}>{editingEquipment ? 'Update' : 'Create'}</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>
      </header>

      {/* Stats Cards */}
      <div className="max-w-full mx-auto px-6 py-6">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Equipment</p>
                  <p className="text-3xl font-bold text-gray-900">{stats.total}</p>
                </div>
                <Building2 className="h-10 w-10 text-primary-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Critical Assets</p>
                  <p className="text-3xl font-bold text-red-600">{stats.critical}</p>
                </div>
                <AlertCircle className="h-10 w-10 text-red-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Warning Status</p>
                  <p className="text-3xl font-bold text-yellow-600">{stats.warning}</p>
                </div>
                <AlertTriangle className="h-10 w-10 text-yellow-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Down/Offline</p>
                  <p className="text-3xl font-bold text-red-600">{stats.down}</p>
                </div>
                <XCircle className="h-10 w-10 text-red-600" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Overdue Maintenance</p>
                  <p className="text-3xl font-bold text-orange-600">{stats.overdue}</p>
                </div>
                <TrendingUp className="h-10 w-10 text-orange-600" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card className="mb-6">
          <CardContent className="p-4">
            <div className="flex flex-wrap gap-4 items-end">
              <div className="flex-1 min-w-[200px] relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
                <Input
                  placeholder="Search by name, tag, location..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
              </div>
              <Select value={categoryFilter} onValueChange={setCategoryFilter}>
                <SelectTrigger className="w-[180px]"><SelectValue placeholder="All Categories" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Categories</SelectItem>
                  {categories.map(c => <SelectItem key={c} value={c}>{c.replace('_', ' ').toUpperCase()}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={criticalityFilter} onValueChange={setCriticalityFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Criticality" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Criticality</SelectItem>
                  {criticalities.map(c => <SelectItem key={c} value={c}>{c.charAt(0).toUpperCase() + c.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
              <Select value={statusFilter} onValueChange={setStatusFilter}>
                <SelectTrigger className="w-[150px]"><SelectValue placeholder="Status" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="">All Status</SelectItem>
                  {statuses.map(s => <SelectItem key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</SelectItem>)}
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Table */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Equipment List ({filteredEquipment.length} of {equipment.length})</CardTitle>
            <div className="flex items-center gap-2">
              <Select value={sortField} onValueChange={setSortField}>
                <SelectTrigger className="w-[180px]"><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="name">Name</SelectItem>
                  <SelectItem value="criticality">Criticality</SelectItem>
                  <SelectItem value="status">Status</SelectItem>
                  <SelectItem value="next_maintenance">Next Maintenance</SelectItem>
                </SelectContent>
              </Select>
              <Button variant="ghost" size="icon" onClick={() => setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc')}>
                {sortOrder === 'asc' ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('name')}>
                      Equipment <ChevronDown className="h-4 w-4 inline ml-1" />
                    </TableHead>
                    <TableHead>Tag</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('criticality')}>
                      Criticality <ChevronDown className="h-4 w-4 inline ml-1" />
                    </TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('status')}>
                      Status <ChevronDown className="h-4 w-4 inline ml-1" />
                    </TableHead>
                    <TableHead>Area</TableHead>
                    <TableHead className="cursor-pointer" onClick={() => handleSort('next_maintenance')}>
                      Next Maintenance <ChevronDown className="h-4 w-4 inline ml-1" />
                    </TableHead>
                    <TableHead className="w-[100px]">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredEquipment.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={8} className="text-center py-8 text-gray-500">
                        No equipment found matching your criteria
                      </TableCell>
                    </TableRow>
                  ) : (
                    filteredEquipment.map((eq) => (
                      <TableRow key={eq.id} className="hover:bg-gray-50">
                        <TableCell className="font-medium">
                          <div>
                            <p>{eq.name}</p>
                            {eq.manufacturer && <p className="text-xs text-gray-500">{eq.manufacturer} {eq.model ? `• ${eq.model}` : ''}</p>}
                          </div>
                        </TableCell>
                        <TableCell className="font-mono text-sm">{eq.tag_number || '-'}</TableCell>
                        <TableCell>
                          <Badge variant="secondary" className="bg-blue-100 text-blue-700">
                            {eq.category.replace('_', ' ').toUpperCase()}
                          </Badge>
                        </TableCell>
                        <TableCell>{getCriticalityBadge(eq.criticality)}</TableCell>
                        <TableCell>{getStatusBadge(eq.status)}</TableCell>
                        <TableCell className="text-sm text-gray-500">{eq.area || '-'}</TableCell>
                        <TableCell className="text-sm font-mono">
                          {eq.next_maintenance_date ? (
                            new Date(eq.next_maintenance_date) < new Date() ? (
                              <span className="text-red-600 font-medium">Overdue: {eq.next_maintenance_date}</span>
                            ) : (
                              eq.next_maintenance_date
                            )
                          ) : '-'}
                        </TableCell>
                        <TableCell>
                          <div className="flex items-center gap-1">
                            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => setSelectedEquipment(eq)}>
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={() => openEditDialog(eq)}>
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button variant="ghost" size="icon" className="h-7 w-7 text-red-600 hover:text-red-700" onClick={() => handleDelete(eq.id)}>
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Detail Dialog */}
      <Dialog open={!!selectedEquipment} onOpenChange={(open) => !open && setSelectedEquipment(null)}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          {selectedEquipment && (
            <div className="space-y-6">
              <DialogHeader>
                <div className="flex items-start justify-between">
                  <div>
                    <DialogTitle>{selectedEquipment.name}</DialogTitle>
                    <p className="text-gray-500">{selectedEquipment.tag_number}</p>
                  </div>
                  <div className="flex items-center gap-2">
                    {getCriticalityBadge(selectedEquipment.criticality)}
                    {getStatusBadge(selectedEquipment.status)}
                  </div>
                </div>
              </DialogHeader>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-gray-500">Category</p>
                  <p className="font-medium">{selectedEquipment.category.replace('_', ' ').toUpperCase()}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Manufacturer</p>
                  <p className="font-medium">{selectedEquipment.manufacturer || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Model</p>
                  <p className="font-medium">{selectedEquipment.model || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Location</p>
                  <p className="font-medium">{selectedEquipment.location || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Area</p>
                  <p className="font-medium">{selectedEquipment.area || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Last Maintenance</p>
                  <p className="font-medium">{selectedEquipment.last_maintenance_date || '-'}</p>
                </div>
                <div>
                  <p className="text-sm text-gray-500">Next Maintenance</p>
                  <p className={cn('font-medium', selectedEquipment.next_maintenance_date && new Date(selectedEquipment.next_maintenance_date) < new Date() ? 'text-red-600' : '')}>
                    {selectedEquipment.next_maintenance_date || '-'}
                    {selectedEquipment.next_maintenance_date && new Date(selectedEquipment.next_maintenance_date) < new Date() && ' (OVERDUE)'}
                  </p>
                </div>
              </div>

              <Tabs defaultValue="issues" className="mt-4">
                <TabsList>
                  <TabsTrigger value="issues">Known Issues</TabsTrigger>
                  <TabsTrigger value="solutions">Solutions</TabsTrigger>
                  <TabsTrigger value="maintenance">Maintenance History</TabsTrigger>
                </TabsList>

                <TabsContent value="issues" className="mt-4">
                  <divide-y divide-gray-200>
                    <p className="text-sm text-gray-500">Common issues for this equipment type will appear here after document ingestion.</p>
                  </TabsContent>
                <TabsContent value="solutions" className="mt-4">
                  <p className="text-sm text-gray-500">Crowdsourced solutions and best practices will appear here.</p>
                </TabsContent>
                <TabsContent value="maintenance" className="mt-4">
                  <p className="text-sm text-gray-500">Maintenance history will be loaded from CMMS integration.</p>
                </TabsContent>
              </Tabs>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}