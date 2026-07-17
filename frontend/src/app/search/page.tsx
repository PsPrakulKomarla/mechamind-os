'use client';

import { useState } from 'react';
import { Search as SearchIcon, FileText, Filter, SlidersHorizontal, ChevronDown, ChevronUp, ExternalLink, Clock, Star, ThumbsUp, Building2, Wrench, ShieldCheck, AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn, formatDateTime } from '@/lib/utils';

interface SearchResult {
  id: string;
  title: string;
  type: 'document' | 'equipment' | 'procedure' | 'compliance' | 'safety';
  excerpt: string;
  relevance: number;
  source: string;
  updated_at: string;
  tags: string[];
}

const mockResults: SearchResult[] = [
  { id: '1', title: 'Pump P-101 Maintenance Manual', type: 'document', excerpt: '...bearing replacement procedure for Pump P-101. Ensure proper alignment before tightening bolts. Torque specifications: 150 Nm...', relevance: 98, source: 'Maintenance Manuals', updated_at: '2026-07-15T10:30:00Z', tags: ['pump', 'maintenance', 'P-101'] },
  { id: '2', title: 'Boiler B-601 Operating Parameters', type: 'procedure', excerpt: '...normal operating pressure: 105 kg/cm². Temperature range: 540°C ± 5°C. Steam flow rate: 600 TPH...', relevance: 95, source: 'Operating Procedures', updated_at: '2026-07-14T14:20:00Z', tags: ['boiler', 'operating', 'parameters'] },
  { id: '3', title: 'Boiler Feed Pump (P-101)', type: 'equipment', excerpt: 'Critical equipment in Unit 1 Power Block. Manufacturer: KSB. Model: WKLN 150/5. Last maintenance: 2024-11-10...', relevance: 92, source: 'Equipment Registry', updated_at: '2026-07-13T09:15:00Z', tags: ['pump', 'equipment', 'P-101'] },
  { id: '4', title: 'OISD-116 Fire Protection Guidelines', type: 'compliance', excerpt: '...fire protection system inspection for pressure vessels must be conducted quarterly. Emergency shutdown testing required...', relevance: 87, source: 'Compliance', updated_at: '2026-07-10T08:30:00Z', tags: ['compliance', 'fire', 'oisd'] },
  { id: '5', title: 'Confined Space Entry Procedure', type: 'safety', excerpt: '...gas test must be performed before entry. Continuous monitoring required. Standby person must be present at all times...', relevance: 85, source: 'Safety Manuals', updated_at: '2026-07-12T16:45:00Z', tags: ['safety', 'confined-space', 'procedure'] },
  { id: '6', title: 'Compressor C-401 Vibration Analysis Report', type: 'document', excerpt: '...vibration levels within acceptable limits. Bearing temperature: 65°C. Recommend next analysis in 3 months...', relevance: 82, source: 'Reports', updated_at: '2026-07-09T13:00:00Z', tags: ['compressor', 'vibration', 'analysis'] },
  { id: '7', title: 'Emergency Shutdown Valve V-301', type: 'equipment', excerpt: 'Main steam emergency shutdown valve. Last tested: 2026-06-15. Requires quarterly functional testing per OISD-116...', relevance: 78, source: 'Equipment Registry', updated_at: '2026-07-08T10:00:00Z', tags: ['valve', 'emergency', 'V-301'] },
  { id: '8', title: 'Annual Maintenance Schedule 2026', type: 'document', excerpt: '...Q3 2026 maintenance window: July 15-20. All critical equipment to be inspected. Planned shutdown for Unit 1...', relevance: 74, source: 'Maintenance Schedules', updated_at: '2026-07-07T15:30:00Z', tags: ['maintenance', 'schedule', 'annual'] },
];

const getTypeIcon = (type: SearchResult['type']) => {
  const icons = {
    document: <FileText className="h-5 w-5 text-blue-500" />,
    equipment: <Building2 className="h-5 w-5 text-orange-500" />,
    procedure: <Wrench className="h-5 w-5 text-indigo-500" />,
    compliance: <ShieldCheck className="h-5 w-5 text-red-500" />,
    safety: <AlertTriangle className="h-5 w-5 text-yellow-500" />,
  };
  return icons[type];
};

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [searched, setSearched] = useState(false);
  const [typeFilter, setTypeFilter] = useState('');
  const [sortBy, setSortBy] = useState<'relevance' | 'date'>('relevance');

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    let filtered = mockResults.filter(r =>
      r.title.toLowerCase().includes(query.toLowerCase()) ||
      r.excerpt.toLowerCase().includes(query.toLowerCase()) ||
      r.tags.some(t => t.toLowerCase().includes(query.toLowerCase()))
    );

    if (typeFilter) {
      filtered = filtered.filter(r => r.type === typeFilter);
    }

    filtered.sort((a, b) => sortBy === 'relevance' ? b.relevance - a.relevance : new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime());

    setResults(filtered);
    setSearched(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-full mx-auto px-6 py-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Smart Search</h1>
            <p className="text-gray-500">Search across documents, equipment, procedures, and more</p>
          </div>
        </div>
      </header>

      <div className="max-w-full mx-auto px-6 py-6">
        {/* Search Bar */}
        <Card className="mb-6">
          <CardContent className="p-6">
            <form onSubmit={handleSearch}>
              <div className="flex gap-3">
                <div className="flex-1 relative">
                  <SearchIcon className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
                  <Input
                    type="search"
                    placeholder="Search equipment, documents, procedures, compliance items..."
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="pl-12 pr-4 py-3 text-lg bg-gray-50 border border-gray-200 rounded-xl focus:ring-2 focus:ring-primary-500"
                  />
                </div>
                <Button type="submit" size="lg" className="px-8">
                  <SearchIcon className="h-5 w-5 mr-2" />
                  Search
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        {/* Filters & Results */}
        {searched && (
          <div className="flex gap-6">
            {/* Sidebar Filters */}
            <div className="w-64 flex-shrink-0 hidden lg:block">
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg flex items-center gap-2">
                    <SlidersHorizontal className="h-4 w-4" />
                    Filters
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Type</label>
                    <Select value={typeFilter} onValueChange={setTypeFilter}>
                      <SelectTrigger><SelectValue placeholder="All Types" /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="">All Types</SelectItem>
                        <SelectItem value="document">Documents</SelectItem>
                        <SelectItem value="equipment">Equipment</SelectItem>
                        <SelectItem value="procedure">Procedures</SelectItem>
                        <SelectItem value="compliance">Compliance</SelectItem>
                        <SelectItem value="safety">Safety</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 mb-2 block">Sort By</label>
                    <Select value={sortBy} onValueChange={(v) => setSortBy(v as typeof sortBy)}>
                      <SelectTrigger><SelectValue /></SelectTrigger>
                      <SelectContent>
                        <SelectItem value="relevance">Relevance</SelectItem>
                        <SelectItem value="date">Date</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <Button variant="outline" className="w-full" onClick={() => { setTypeFilter(''); setSortBy('relevance'); }}>
                    Reset Filters
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Results */}
            <div className="flex-1 min-w-0">
              <p className="text-sm text-gray-500 mb-4">
                Found {results.length} result{results.length !== 1 ? 's' : ''} for "{query}"
              </p>

              <div className="space-y-3">
                {results.map((result) => (
                  <Card key={result.id} className="hover:shadow-md transition-shadow cursor-pointer">
                    <CardContent className="p-5">
                      <div className="flex items-start gap-4">
                        <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center flex-shrink-0">
                          {getTypeIcon(result.type)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-start justify-between gap-4">
                            <div>
                              <h3 className="font-semibold text-gray-900">{result.title}</h3>
                              <p className="text-sm text-gray-500 mt-0.5">{result.source}</p>
                            </div>
                            <div className="flex items-center gap-2 flex-shrink-0">
                              <Badge variant="secondary" className="bg-primary-100 text-primary-700">
                                {result.relevance}% match
                              </Badge>
                              <Button variant="ghost" size="icon" className="h-7 w-7">
                                <ExternalLink className="h-4 w-4" />
                              </Button>
                            </div>
                          </div>
                          <p className="text-sm text-gray-600 mt-2 leading-relaxed">{result.excerpt}</p>
                          <div className="flex items-center gap-3 mt-3">
                            <div className="flex flex-wrap gap-1">
                              {result.tags.map(tag => (
                                <Badge key={tag} variant="secondary" className="text-xs bg-gray-100 text-gray-600">{tag}</Badge>
                              ))}
                            </div>
                            <span className="text-xs text-gray-400 flex items-center gap-1 ml-auto">
                              <Clock className="h-3 w-3" />
                              {formatDateTime(result.updated_at)}
                            </span>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}

                {results.length === 0 && (
                  <Card>
                    <CardContent className="p-12 text-center">
                      <SearchIcon className="h-16 w-16 mx-auto text-gray-300 mb-4" />
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No results found</h3>
                      <p className="text-gray-500">Try adjusting your search terms or filters</p>
                    </CardContent>
                  </Card>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Initial State */}
        {!searched && (
          <div className="text-center py-20">
            <SearchIcon className="h-20 w-20 mx-auto text-gray-300 mb-6" />
            <h2 className="text-2xl font-semibold text-gray-900 mb-2">Search your knowledge base</h2>
            <p className="text-gray-500 max-w-md mx-auto">
              Find documents, equipment details, procedures, compliance requirements, and safety information across your entire industrial knowledge base.
            </p>
            <div className="flex flex-wrap gap-2 justify-center mt-6">
              {['Pump P-101', 'Boiler B-601', 'OISD-116', 'Confined space', 'Vibration analysis', 'Maintenance schedule'].map(suggestion => (
                <Button
                  key={suggestion}
                  variant="outline"
                  size="sm"
                  onClick={() => { setQuery(suggestion); }}
                >
                  {suggestion}
                </Button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}